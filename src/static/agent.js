let activeConversationId = null;
let currentSessionKey = null;
let isConfirmationRequired = false;
let isAutoConfirmationEnabled = false;

function getConversationDiv(conversationId) {
  return $(`#conversation-${conversationId}`);
}

function getActiveConversationDiv() {
  return getConversationDiv(activeConversationId);
}

function scrollToBottom() {
  // Only scroll if the active conversation is visible
  if (activeConversationId !== null &&
      getActiveConversationDiv().is(':visible'))
    window.scrollTo(0, document.body.scrollHeight);
}

function countMessages() {
  if (activeConversationId === null) return 0;
  return getActiveConversationDiv().find('.message').length;
}

function requestMessages(socket, conversationId) {
  socket.emit(
      'request_update',
      {message_count: countMessages(), conversation_id: conversationId});
}

function updateConfirmationUI() {
  const $confirmationInput = $('#confirmation_input');
  $confirmationInput.prop('disabled', !isConfirmationRequired);
  if (isConfirmationRequired) {
    $confirmationInput.attr('placeholder', 'Confirmation…');
    $confirmationInput.focus();
    setTimeout(() => {
      $confirmationInput.css('height', 'auto');
      $confirmationInput.height($confirmationInput[0].scrollHeight);
    }, 0);
  } else {
    $confirmationInput.val('');
    $confirmationInput.attr('placeholder', '');
    $confirmationInput.css('height', 'auto');
  }
}

function sendConfirmation(socket, confirmationMessage) {
  socket.emit('confirm', {
    confirmation: confirmationMessage,
    message_count: countMessages(),
    conversation_id: activeConversationId
  });
  console.log('CONFIRMATION: Send confirmation.')
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
    sendConfirmation(socket, '');
  }
  updateConfirmationUI();
}

function showConversation(conversationId) {
  $('.conversation').hide();  // Hide all.
  activeConversationId = conversationId;
  const $targetConversation = getActiveConversationDiv();
  if ($targetConversation.length === 0) {
    console.warn(`Conversation div for ID ${conversationId} not found.`);
    return;
  }
  $targetConversation.show();  // Show the selected one
  const $conversationSelector = $('#conversation_selector');
  if (parseInt($conversationSelector.val()) !== conversationId)
    $conversationSelector.val(conversationId);
  scrollToBottom();
}

function handleUpdate(socket, data) {
  console.log('Starting update');
  console.log(data);

  const conversationId = data.conversation_id;
  const conversationName =
      data.conversation_name || `Conversation ${conversationId}`;

  const $conversationSelector = $('#conversation_selector');
  let $option = $conversationSelector.find(`option[value="${conversationId}"]`);
  if ($option.length === 0) {
    console.log('Creating selector...');
    $option = $('<option>').val(conversationId);
    $conversationSelector.append($option);
  }
  $option.text(conversationName);
  $conversationSelector.val(conversationId);

  if (currentSessionKey !== data.session_key) {
    console.log('Session key changed. Clearing conversation.');
    $('#conversation_container').empty();
    currentSessionKey = data.session_key;
  }

  let $conversationDiv = $(`#conversation-${conversationId}`);
  if ($conversationDiv.length === 0) {
    console.log(`Creating container for conversation ${conversationId}`);
    $conversationDiv = $('<div>')
                           .addClass('conversation')
                           .attr('id', `conversation-${conversationId}`)
                           .hide();
    $('#conversation_container').append($conversationDiv);
  }

  const currentMessagesInDiv = $conversationDiv.find('.message').length;
  data.conversation
      .slice(Math.max(0, currentMessagesInDiv - data.first_message_index))
      .forEach(message => {
        const $messageDiv = $('<div>').addClass('message');
        const $role = $('<p>').addClass('role').text(`${message.role}:`);

        const $contentContainer = $('<div>').addClass('content-container');
        (message.content_sections || []).forEach(section => {
          const $sectionDiv = $('<div>').addClass('messageSection');
          const lineCount = section.content.length;
          const $fullContentPre = $('<pre>')
                                      .addClass('full-content-pre')
                                      .text(section.content.join('\n'));

          if (lineCount <= 5) {
            $sectionDiv.append($fullContentPre);
          } else {
            const firstLineContent =
                section.summary || section.content[0] || '';
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
        $conversationDiv.append($messageDiv);
      });

  showConversation(conversationId);
  isConfirmationRequired = data.confirmation_required;
  console.log(`CONFIRMATION: Signal from server: {isConfirmationRequired}`)
  maybeAutoConfirm(socket);

  if (data.message_count > currentMessagesInDiv)
    requestMessages(socket, conversationId);
}

document.addEventListener('DOMContentLoaded', function() {
  const socket = io();
  socket.on('update', (data) => handleUpdate(socket, data));

  const confirmationForm = document.getElementById('confirmation_form');
  const confirmationInput = document.getElementById('confirmation_input');
  const autoConfirmCheckbox = document.getElementById('auto_confirm_checkbox');
  // Need to ensure these elements exist in the HTML (select for conversations,
  // and container for conversation divs) Assuming they will be added to
  // index.html as part of this feature.
  const $conversationSelector = $('#conversation_selector');

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
        // Allow shift+enter for new line
      } else {
        event.preventDefault();
        if (isConfirmationRequired) $(confirmationForm).submit();
      }
    }
  });

  $(confirmationForm).on('submit', function(event) {
    event.preventDefault();
    sendConfirmation(socket, confirmationInput.value);
    updateConfirmationUI();
  });

  $conversationSelector.on('change', function() {
    // When user changes selection, show that conversation
    showConversation(parseInt($(this).val()));
  });

  console.log('Requesting initial update.');
  const initialConversationId = 0;
  requestMessages(socket, initialConversationId);

  updateConfirmationUI();
});
