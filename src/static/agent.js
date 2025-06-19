function scrollToBottom() {
  window.scrollTo(0, document.body.scrollHeight);
}

function handleUpdate(data) {
  console.log('Starting update');
  console.log(data);

  const $conversation = $('#conversation');
  $conversation.empty();
  data.conversation.forEach(message => {
    const $messageDiv = $('<div>').addClass('message');
    const $role = $('<p>').addClass('role').text(`${message.role}:`);
    const $content = $('<div>').addClass('content').append(
        $('<pre>').text(message.content)  // `.text()` auto-escapes
    );

    $messageDiv.append($role, $content);
    $conversation.append($messageDiv);
  });

  $('#confirmButton').prop('disabled', !data.confirmation_required);
  scrollToBottom();
}

document.addEventListener('DOMContentLoaded', function() {
  const socket = io();
  socket.on('update', handleUpdate)

  const confirmationForm = document.getElementById('confirmation_form');
  confirmationForm.addEventListener('submit', function(event) {
    event.preventDefault();  // Prevent the form from submitting traditionally
    const textElement = confirmationForm.elements['confirmation']
    socket.emit('confirm', {confirmation: textElement.value});
    $('#confirmButton').prop('disabled', true);
    textElement.value = '';
  });

  console.log('Requesting update.');
  socket.emit('request_update', {});
});
