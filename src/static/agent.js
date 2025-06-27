let activeConversationId = null;
let currentSessionKey = null;
let isConfirmationRequired = false;
let isAutoConfirmationEnabled = false;

function getConversationDiv(conversationId) {
  return $(`#conversation-${conversationId}`);
}

function getOrCreateConversationDiv(conversationId) {
  let $conversationDiv = getConversationDiv(conversationId);
  if ($conversationDiv.length === 0) {
    console.log(`Creating container for conversation ${conversationId}`);
    $conversationDiv = $('<div>')
                           .addClass('conversation')
                           .attr('id', `conversation-${conversationId}`)
                           .hide();
    $('#conversation_container').append($conversationDiv);
  }
  return $conversationDiv;
}

function updateConversationSelectorOption(conversationId, conversationName) {
  const $conversationSelector = $('#conversation_selector');
  let $option = $conversationSelector.find(`option[value="${conversationId}"]`);
  if ($option.length === 0) {
    $option = $('<option>').val(conversationId);
    $conversationSelector.append($option);
  }
  $option.text(conversationName);
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

function countMessages(conversationId) {
  if (conversationId === null) return 0;
  const $conversationDiv = getConversationDiv(conversationId);
  if ($conversationDiv.length === 0) return 0;
  return $conversationDiv.find('.message').length;
}

function requestMessages(socket, conversationId) {
  socket.emit('request_update', {
    message_count: countMessages(conversationId),
    conversation_id: conversationId
  });
}

function updateConfirmationUI() {
  const $confirmationInput = $('#confirmation_input');
  $confirmationInput.prop('disabled', !isConfirmationRequired);
  if (isConfirmationRequired) {
    $confirmationInput.attr('placeholder', 'Confirmation…');
    $confirmationInput.focus();
  } else {
    $confirmationInput.val('');
    $confirmationInput.attr('placeholder', '');
  }
}

function sendConfirmation(socket, confirmationMessage) {
  socket.emit('confirm', {
    confirmation: confirmationMessage,
    message_count: countMessages(activeConversationId),
    conversation_id: activeConversationId
  });
  console.log('Confirmation: Send confirmation.')
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

function addMessage($conversationDiv, message) {
  const $messageDiv = $('<div>').addClass('message');
  const $role = $('<p>').addClass('role').text(`${message.role}:`);

  const creationTimestamp = new Date(message.creation_time).getTime();
  const $timestampView = createTimestampView(creationTimestamp);
  $timestampView.addClass('timestamp');

  const $messageHeader = $('<div>').addClass('message-header');
  $messageHeader.append($role, $timestampView);

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
      const firstLineContent = section.summary || section.content[0] || '';
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
      const $lineCountSpan =
          $('<span>').addClass('line-count').text(` (${lineCount} lines)`);

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

  $messageDiv.append($messageHeader, $contentContainer);
  $conversationDiv.append($messageDiv);
}

function handleUpdate(socket, data) {
  console.log('Starting update');
  console.log(data);

  const conversationId = data.conversation_id;
  const conversationName =
      data.conversation_name || `Conversation ${conversationId}`;

  updateConversationSelectorOption(conversationId, conversationName);
  $('#conversation_selector').val(conversationId);

  if (currentSessionKey !== data.session_key) {
    console.log('Session key changed. Clearing conversation.');
    $('#conversation_container').empty();
    currentSessionKey = data.session_key;
  }

  const $conversationDiv = getOrCreateConversationDiv(conversationId);

  const currentMessagesInDiv = countMessages(conversationId);
  data.conversation
      .slice(Math.max(0, currentMessagesInDiv - data.first_message_index))
      .forEach(message => {
        addMessage($conversationDiv, message);
      });

  showConversation(conversationId);

  const conversationState = data.conversation_state;
  if (conversationState) {
    const $confirmationForm = $('#confirmation_form');
    const $stateDisplay = $('#conversation_state_display');
    if (conversationState === 'WAITING_FOR_CONFIRMATION') {
      $stateDisplay.hide();
      $confirmationForm.show();
    } else {
      $confirmationForm.hide();
      const prettyState = conversationState.replace(/_/g, ' ').toLowerCase();
      $stateDisplay
          .text(prettyState.charAt(0).toUpperCase() + prettyState.slice(1))
          .show();
    }
  }

  isConfirmationRequired = data.confirmation_required;
  console.log(`Confirmation: Signal from server: ${conversationId}: ${
      isConfirmationRequired}`)
  maybeAutoConfirm(socket);

  if (data.message_count > countMessages(conversationId))
    requestMessages(socket, conversationId);
}

function handleListConversations(socket, conversations) {
  console.log('Received conversation list:', conversations);

  conversations.forEach(conversation => {
    const conversationId = conversation.id;
    const conversationName = conversation.name;
    // TODO: Handle `conversation.state`

    updateConversationSelectorOption(conversationId, conversationName);

    getOrCreateConversationDiv(conversationId);

    const clientMessageCount = countMessages(conversationId);
    if (conversation.message_count > clientMessageCount) {
      console.log(
          `Client has ${clientMessageCount} messages for convo ` +
          `${conversationId}, server has ${conversation.message_count}. ` +
          `Requesting update.`);
      requestMessages(socket, conversationId);
    }
  });
}

document.addEventListener('DOMContentLoaded', function() {
  const socket = io();
  socket.on('update', (data) => handleUpdate(socket, data));
  socket.on(
      'list_conversations', (data) => handleListConversations(socket, data));

  const confirmationForm = document.getElementById('confirmation_form');
  const confirmationInput = document.getElementById('confirmation_input');
  const autoConfirmCheckbox = document.getElementById('auto_confirm_checkbox');
  const $conversationSelector = $('#conversation_selector');

  loadAutoConfirmState();
  autoConfirmCheckbox.checked = isAutoConfirmationEnabled;

  autoConfirmCheckbox.addEventListener('change', function() {
    isAutoConfirmationEnabled = this.checked;
    saveAutoConfirmState();
    console.log('Automatic confirmation is now:', isAutoConfirmationEnabled);
    maybeAutoConfirm(socket);
  });

  $(confirmationInput).on('input', scrollToBottom);

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

  console.log('Requesting conversation list.');
  socket.emit('list_conversations');

  updateConfirmationUI();
});
