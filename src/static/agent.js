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

function handleUpdate(socket, data) {
  console.log('Starting update');
  console.log(data);

  if (currentSessionKey !== data.session_key) {
    console.log('Session key changed. Clearing conversation.');
    $('#conversation').empty();
    currentSessionKey = data.session_key;
  }

  const $conversation = $('#conversation');
  data.conversation.forEach(message => {
    const $messageDiv = $('<div>').addClass('message');
    const $role = $('<p>').addClass('role').text(`${message.role}:`);

    const $collapseLink =
        $('<span>').addClass('toggle-link collapse').text('[collapse]');
    const $expandLink =
        $('<span>').addClass('toggle-link expand').text('[expand]').hide();

    const $content =
        $('<div>').addClass('content').append($('<pre>').text(message.content));

    $collapseLink.on('click', () => {
      $content.hide();
      $collapseLink.hide();
      $expandLink.show();
    });

    $expandLink.on('click', () => {
      $content.show();
      $collapseLink.show();
      $expandLink.hide();
    });

    $role.append($collapseLink, $expandLink);
    $messageDiv.append($role, $content);
    $conversation.append($messageDiv);
  });

  // Update confirmation required state and form visibility
  isConfirmationRequired = data.confirmation_required;
  const $confirmationForm = $('#confirmation_form');
  const $confirmationInput = $('#confirmation_input');

  if (isConfirmationRequired) {
    $confirmationForm.css('display', 'block');
    $confirmationInput.focus();
  } else {
    $confirmationForm.css('display', 'none');
  }

  // Auto-resize textarea after updates if it's visible
  if ($confirmationInput.is(':visible')) {
    $confirmationInput.css('height', 'auto');
    $confirmationInput.css('height', $confirmationInput[0].scrollHeight + 'px');
  }

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
    confirmationInput.value = '';
    confirmationInput.style.height = 'auto';
  });

  console.log('Requesting update.');
  socket.emit('request_update', {message_count: countMessages()});
});
