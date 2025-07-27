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
      'auto_confirm_enabled', JSON.stringify(autoConfirmCheckbox().checked));
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
      data.conversation_state_emoji,
      new Date(data.last_state_change_time).getTime());

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
        new Date(data.last_state_change_time).getTime());
    conversation.updateView();
    maybeRequestMessages(socket, data.message_count, conversation);
  });
}

function switchSelectedConversationIndex(delta) {
  const $conversationSelector = $('#conversation_selector');
  const currentLength = $conversationSelector.children('option').length;
  if (currentLength === 0) return; // No conversations to switch

  let newIndex = $conversationSelector.prop('selectedIndex') + delta;

  // Wrap around logic
  if (newIndex < 0) {
    newIndex = currentLength - 1;
  } else if (newIndex >= currentLength) {
    newIndex = 0;
  }

  $conversationSelector.prop('selectedIndex', newIndex);
  $conversationSelector.trigger('change');
}

document.addEventListener('DOMContentLoaded', function() {
  const socket = io();
  socket.on('update', (data) => handleUpdate(socket, data));
  socket.on(
      'list_conversations', (data) => handleListConversations(socket, data));

  const confirmationForm = document.getElementById('confirmation_form');
  const confirmationInput = document.getElementById('confirmation_input');
  const confirmButton = document.getElementById('confirm_button');
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

  $(confirmButton).on('click', function() {
    const shownConversation = getShownConversation();
    if (shownConversation != null &&
        shownConversation.isWaitingForConfirmation())
      $(confirmationForm).submit();
  });

  $(confirmationForm).on('submit', function(event) {
    event.preventDefault();
    sendConfirmation(socket, confirmationInput.value);
  });

  $conversationSelector.on('change', function() {
    const id = parseInt($(this).val());
    if (conversationsById[id]) conversationsById[id].show();
  });

  // Function to show/hide the confirmation button
  function updateConfirmationButtonVisibility() {
    const confirmationForm = document.getElementById('confirmation_form');
    if (confirmationForm.style.display === 'none') {
      confirmButton.style.display = 'none';
    } else {
      confirmButton.style.display = 'inline-block'; // Or 'block' depending on desired layout
    }
  }

  // Observe changes to the style attribute of the confirmation_form
  const observer = new MutationObserver(function(mutations) {
    mutations.forEach(function(mutation) {
      if (mutation.attributeName === 'style') {
        updateConfirmationButtonVisibility();
      }
    });
  });

  observer.observe(confirmationForm, { attributes: true });

  // Initial check for button visibility
  updateConfirmationButtonVisibility();

  $('#prev_conversation_button').on('click', function() {
    switchSelectedConversationIndex(-1);
  });

  $('#next_conversation_button').on('click', function() {
    switchSelectedConversationIndex(1);
  });

  console.log('Requesting conversation list.');
  socket.emit('list_conversations');
});
