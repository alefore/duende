function scrollToBottom() {
  window.scrollTo(0, document.body.scrollHeight);
}

let currentSessionKey = null;
let isConfirmationRequired = false;
let isAutoConfirmationEnabled = false;

function countMessages() {
  return $('#conversation .message').length;
}

function requestMessages(socket) {
  socket.emit('request_update', {message_count: countMessages()});
}

function updateConfirmationUI() {
  const $confirmationInput = $('#confirmation_input');
  $confirmationInput.prop('disabled', !isConfirmationRequired);
  if (isConfirmationRequired) {
    $confirmationInput.focus();
    setTimeout(() => {
      $confirmationInput.css('height', 'auto');
      $confirmationInput.height($confirmationInput[0].scrollHeight);
    }, 0);
  } else {
    $confirmationInput.val('');
    $confirmationInput.css('height', 'auto');
  }
}

function sendConfirmation(confirmationMessage) {
  socket.emit(
      'confirm',
      {confirmation: confirmationMessage, message_count: countMessages()});
  isConfirmationRequired = false;
}

function loadAutoConfirmState() {
  const savedState = localStorage.getItem('auto_confirm_enabled');
  if (savedState !== null) {
    isAutoConfirmationEnabled = JSON.parse(savedState);
  }
}

function saveAutoConfirmState() {
  localStorage.setItem(
      'auto_confirm_enabled', JSON.stringify(isAutoConfirmationEnabled));
}

function maybeAutoConfirm(socket) {
  if (isConfirmationRequired && isAutoConfirmationEnabled) {
    console.log('Automatic confirmation enabled. Sending empty confirmation.');
    sendConfirmation('');
  }
  updateConfirmationUI();
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

  isConfirmationRequired = data.confirmation_required;
  maybeAutoConfirm(socket);

  if (data.message_count > countMessages()) requestMessages(socket);
  scrollToBottom();
}

document.addEventListener('DOMContentLoaded', function() {
  const socket = io();
  socket.on('update', (data) => handleUpdate(socket, data));

  const confirmationForm = document.getElementById('confirmation_form');
  const confirmationInput = document.getElementById('confirmation_input');
  const autoConfirmCheckbox = document.getElementById('auto_confirm_checkbox');

  loadAutoConfirmState();
  autoConfirmCheckbox.checked = isAutoConfirmationEnabled;

  autoConfirmCheckbox.addEventListener('change', function() {
    isAutoConfirmationEnabled = this.checked;
    saveAutoConfirmState();
    console.log('Automatic confirmation is now:', isAutoConfirmationEnabled);
    maybeAutoConfirm(socket);
  });

  $(confirmationInput).on('input', function() {
    this.style.height = 'auto';
    this.style.height = this.scrollHeight + 'px';
    scrollToBottom();
  });

  $(confirmationInput).on('keydown', function(event) {
    if (event.key === 'Enter') {
      if (event.shiftKey) {
      } else {
        event.preventDefault();
        if (isConfirmationRequired) $(confirmationForm).submit();
      }
    }
  });

  $(confirmationForm).on('submit', function(event) {
    event.preventDefault();
    sendConfirmation(confirmationInput.value);
    updateConfirmationUI();
  });

  console.log('Requesting initial update.');
  socket.emit('request_update', {message_count: countMessages()});

  updateConfirmationUI();
});
