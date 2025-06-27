let currentSessionKey = null;
const conversationsById = {};

function autoConfirmCheckbox() {
  return document.getElementById('auto_confirm_checkbox');
}

function getShownConversation() {
  if (shownConversationId === null) return null;
  console.log(conversationsById);
  console.log(shownConversationId);
  return conversationsById[shownConversationId];
}

function createOrUpdateConversation(
    id, name, state, stateEmoji, lastStateChangeTime) {
  if (conversationsById[id])
    conversationsById[id].updateData(
        name, state, stateEmoji, lastStateChangeTime);
  else
    conversationsById[id] =
        new ConversationData(id, name, state, stateEmoji, lastStateChangeTime);
  return conversationsById[id].updateView();
}

function scrollToBottom() {
  if (shownConversationId !== null && getShownConversation().div.is(':visible'))
    window.scrollTo(0, document.body.scrollHeight);
}

function requestMessages(socket, conversation) {
  const data = {
    message_count: conversation.countMessages(),
    conversation_id: conversation.id
  };
  console.log(data);
  socket.emit('request_update', data);
}

function sendConfirmation(socket, confirmationMessage) {
  socket.emit('confirm', {
    confirmation: confirmationMessage,
    message_count: getShownConversation().countMessages(),
    conversation_id: shownConversationId
  });
  getShownConversation().notifyConfirmationSent().updateView();
}

function loadAutoConfirmState() {
  const savedState = localStorage.getItem('auto_confirm_enabled');
  if (savedState !== null)
    autoConfirmCheckbox().checked = JSON.parse(savedState);
}

function saveAutoConfirmState() {
  localStorage.setItem(
      'auto_confirm_enabled', JSON.stringify(autoConfirmCheckbox.checked));
}

function maybeAutoConfirm(socket) {
  if (getShownConversation().isWaitingForConfirmation() &&
      autoConfirmCheckbox().checked) {
    console.log('Automatic confirmation enabled. Sending empty confirmation.');
    sendConfirmation(socket, '');
    showActiveConversationState();
  }
}

function maybeRequestMessages(socket, serverMessages, conversation) {
  if (serverMessages > conversation.countMessages()) {
    console.log(
        `Client has ${conversation.countMessages()} messages for ` +
        `${conversation.id}, server has ${serverMessages}. ` +
        `Requesting update.`);
    requestMessages(socket, conversation);
  }
}

function handleUpdate(socket, data) {
  console.log('Starting update');
  console.log(data);

  if (currentSessionKey !== data.session_key) {
    console.log('Session key changed. Clearing conversation.');
    $('#conversation_container').empty();
    Object.keys(conversationsById)
        .forEach(key => delete conversationsById[key]);
    $('#conversation_selector').empty();
    shownConversationId = null;
    currentSessionKey = data.session_key;
  }

  const conversation = createOrUpdateConversation(
      data.conversation_id, data.conversation_name, data.conversation_state,
      data.conversation_state_emoji, data.last_state_change_time);

  data.conversation
      .slice(
          Math.max(0, conversation.countMessages() - data.first_message_index))
      .forEach(message => {
        conversation.addMessage(message);
      });

  conversation.updateView();
  if (conversation.isShown()) maybeAutoConfirm(socket);
  maybeRequestMessages(socket, data.message_count, conversation);
}

function handleListConversations(socket, conversations) {
  console.log('Received conversation list:', conversations);
  conversations.forEach(data => {
    const conversation = createOrUpdateConversation(
        data.id, data.name, data.state, data.state_emoji,
        data.last_state_change_time);
    conversation.updateView();
    maybeRequestMessages(socket, data.message_count, conversation);
  });
}

document.addEventListener('DOMContentLoaded', function() {
  const socket = io();
  socket.on('update', (data) => handleUpdate(socket, data));
  socket.on(
      'list_conversations', (data) => handleListConversations(socket, data));

  const confirmationForm = document.getElementById('confirmation_form');
  const confirmationInput = document.getElementById('confirmation_input');
  const $conversationSelector = $('#conversation_selector');

  loadAutoConfirmState();
  autoConfirmCheckbox().addEventListener('change', function() {
    saveAutoConfirmState();
    maybeAutoConfirm(socket);
  });

  $(confirmationInput).on('input', scrollToBottom);

  $(confirmationInput).on('keydown', function(event) {
    if (event.key === 'Enter') {
      if (event.shiftKey) {
        // Allow shift+enter for new line
      } else {
        event.preventDefault();
        const shownConversation = getShownConversation();
        if (shownConversation != null &&
            shownConversation.isWaitingForConfirmation())
          $(confirmationForm).submit();
      }
    }
  });

  $(confirmationForm).on('submit', function(event) {
    event.preventDefault();
    sendConfirmation(socket, confirmationInput.value);
    showConversationState(getShownConversation());
  });

  $conversationSelector.on('change', function() {
    showConversation(parseInt($(this).val()));
  });

  console.log('Requesting conversation list.');
  socket.emit('list_conversations');
});
