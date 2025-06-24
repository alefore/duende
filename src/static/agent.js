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
    // More robust auto-grow for initial display:
    // Reset height, then set to scrollHeight. Use setTimeout to ensure DOM is
    // ready.
    setTimeout(() => {
      $confirmationInput.css(
          'height', 'auto');  // Ensure height is not fixed by previous input
      $confirmationInput.height($confirmationInput[0].scrollHeight);
    }, 0);
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

        const $contentContainer = $('<div>').addClass('content-container');
        (message.content_sections || []).forEach(section => {
          const $sectionDiv = $('<div>').addClass('messageSection');
          const lineCount = section.length;
          const $fullContentPre =
              $('<pre>').addClass('full-content-pre').text(section.join('\n'));

          if (lineCount <= 5) {
            $sectionDiv.append($fullContentPre);
          } else {
            const firstLineContent = section[0] || '';
            const $firstLinePre =
                $('<pre>')
                    .addClass('first-line-pre')
                    .text(
                        firstLineContent.length > 100 ?
                            firstLineContent.substring(0, 100) + '...' :
                            firstLineContent);

            const $sectionHeader = $('<div>').addClass('section-header');
            const $expandLink =
                $('<span>').addClass('toggle-link expand').text('[expand]');
            const $collapseLink = $('<span>')
                                      .addClass('toggle-link collapse')
                                      .text('[collapse]')
                                      .hide();
            const $lineCountSpan = $('<span>')
                                       .addClass('line-count')
                                       .text(` (${lineCount} lines)`);

            $sectionHeader.append($expandLink, $collapseLink, $lineCountSpan);
            $sectionDiv.append($sectionHeader, $firstLinePre, $fullContentPre);

            $expandLink.on('click', () => {
              $fullContentPre.show();
              $firstLinePre.hide();
              $expandLink.hide();
              $lineCountSpan.hide();
              $collapseLink.show();
            });

            $collapseLink.on('click', () => {
              $fullContentPre.hide();
              $firstLinePre.show();
              $expandLink.show();
              $lineCountSpan.show();
              $collapseLink.hide();
            });
            $collapseLink.click();
          }
          $contentContainer.append($sectionDiv);
        });

        $messageDiv.append($role, $contentContainer);
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
    this.style.height = 'auto';  // Reset height to auto to allow shrinking and
                                 // proper scrollHeight calculation
    this.style.height =
        this.scrollHeight + 'px';  // Set to actual scroll height
    scrollToBottom();
  });

  // Handle Enter/Shift+Enter for submission and new line
  $(confirmationInput).on('keydown', function(event) {
    if (event.key === 'Enter') {
      if (event.shiftKey) {
        // If Shift+Enter, allow default behavior (new line).
        // This will also trigger the 'input' event, which handles auto-grow.
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
  // starts disabled and with correct height.
  updateConfirmationUI(isConfirmationRequired);
});
