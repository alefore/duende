function scrollToBottom() {
  window.scrollTo(0, document.body.scrollHeight);
}

let currentSessionKey = null;

function handleUpdate(data) {
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

  $('#confirmButton').prop('disabled', !data.confirmation_required);
  scrollToBottom();
}

function countMessages() {
  return $('#conversation .message').length;
}

document.addEventListener('DOMContentLoaded', function() {
  const socket = io();
  socket.on('update', handleUpdate);

  const confirmationForm = document.getElementById('confirmation_form');
  confirmationForm.addEventListener('submit', function(event) {
    event.preventDefault();
    const textElement = confirmationForm.elements['confirmation'];
    socket.emit(
        'confirm',
        {confirmation: textElement.value, message_count: countMessages()});
    $('#confirmButton').prop('disabled', true);
    textElement.value = '';
  });

  console.log('Requesting update.');
  socket.emit('request_update', {message_count: countMessages()});
});
