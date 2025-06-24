function scrollToBottom() {
  window.scrollTo(0, document.body.scrollHeight);
}

let currentSessionKey = null;
let isConfirmationRequired = false;

function countMessages() {
  return $('#conversation .message').length;
}

function requestMessages(socket) {
  socket.emit('request_update', {message_count: countMessages()});
}

function updateConfirmationUI(required) {
  const $confirmationForm = $('#confirmation_form');
  const $confirmationInput = $('#confirmation_input');

  $confirmationInput.prop('disabled', !required);
  if (required) {
    $confirmationInput.focus();
    $confirmationInput.css('height', 'auto');
    $confirmationInput.css('height', $confirmationInput[0].scrollHeight + 'px');
  } else {
    $confirmationInput.val('');                // Clear content
    $confirmationInput.css('height', 'auto');  // Reset height
  }
}

function handleUpdate(socket, data) {
  console.log('Starting update');
  console.log(data);

  if (currentSessionKey !== data.session_key) {
    console.log('Session key changed. Clearing conversation.');
    $('#conversation').empty();
    currentSessionKey = data.session_key;
  }

  const $conversation = $('#conversation');

  data.conversation
      .slice(Math.max(0, countMessages() - data.first_message_index))
      .forEach(message => {
        const $messageDiv = $('<div>').addClass('message');
        const $role = $('<p>').addClass('role').text(`${message.role}:`);

        // Create collapse/expand links for the entire message content
        const $collapseLink =
            $('<span>').addClass('toggle-link collapse').text('[collapse]');
        const $expandLink =
            $('<span>').addClass('toggle-link expand').text('[expand]').hide();

        const $contentContainer = $('<div>').addClass('content-container');
        (message.content_sections || []).forEach(section => {
          const $sectionDiv = $('<div>').addClass('messageSection');
          $sectionDiv.append($('<pre>').text(section.join('\n')));
          $contentContainer.append($sectionDiv);
        });

        $collapseLink.on('click', () => {
          $contentContainer.hide();
          $collapseLink.hide();
          $expandLink.show();
        });

        $expandLink.on('click', () => {
          $contentContainer.show();
          $collapseLink.show();
          $expandLink.hide();
        });

        $role.append($collapseLink, $expandLink);
        $messageDiv.append($role, $contentContainer);  // Append the container
        $conversation.append($messageDiv);
      });

  // Update confirmation required state and form visibility
  isConfirmationRequired = data.confirmation_required;
  updateConfirmationUI(isConfirmationRequired);

  if (data.message_count > countMessages()) requestMessages(socket);
  scrollToBottom();
}

document.addEventListener('DOMContentLoaded', function() {
  const socket = io();
  socket.on('update', (data) => handleUpdate(socket, data));

  const confirmationForm = document.getElementById('confirmation_form');
  const confirmationInput = document.getElementById(
      'confirmation_input');  // Get the textarea element

  // Auto-grow textarea on input
  $(confirmationInput).on('input', function() {
    this.style.height = 'auto';
    this.style.height = (this.scrollHeight) + 'px';
    scrollToBottom();
  });

  // Handle Enter/Shift+Enter for submission and new line
  $(confirmationInput).on('keydown', function(event) {
    if (event.key === 'Enter') {
      if (event.shiftKey) {
        // If Shift+Enter, allow default behavior (new line).
      } else {
        event.preventDefault();
        if (isConfirmationRequired) $(confirmationForm).submit();
      }
    }
  });

  $(confirmationForm).on('submit', function(event) {
    event.preventDefault();
    socket.emit('confirm', {
      confirmation: confirmationInput.value,
      message_count: countMessages()
    });
    // Immediately update UI to reflect "no confirmation required" state
    updateConfirmationUI(false);
  });

  console.log('Requesting initial update.');
  socket.emit('request_update', {message_count: countMessages()});

  // Call updateConfirmationUI initially to set the correct state based on
  // `isConfirmationRequired` which is false by default, ensuring the textarea
  // starts disabled.
  updateConfirmationUI(isConfirmationRequired);
});
