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

    // Create collapse/expand links
    const $collapseLink =
        $('<span>').addClass('toggle-link collapse').text('[collapse]');
    const $expandLink =
        $('<span>').addClass('toggle-link expand').text('[expand]').hide();

    // Create the content and manage its initial state
    const $content = $('<div>').addClass('content').append(
        $('<pre>').text(message.content)  // `.text()` auto-escapes
    );

    // Add click events for toggling
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
