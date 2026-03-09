function renderConversationsTable(conversationsById) {
  const $div = $('#conversations_table_view');
  $div.empty();

  const $tableBody = $div.append($('<table>')).append($('<tbody>'));
  for (const id in conversationsById) {
    const conversation = conversationsById[id];
    const $row = $('<tr>');

    // Title
    $row.append($('<td>').text(conversation.name));

    // Messages Count
    $row.append($('<td>').text(conversation.countMessages()));

    // State
    $row.append($('<td>').text(`${conversation.stateEmoji} ${
        conversation.state.replace(/_/g, ' ').toLowerCase()}`));

    // Last Message Overview
    $row.append($('<td>').text(conversation.getLastMessageOverview()));

    $row.on('click', function() {
      conversation.show();
      $('#conversations_table_view').hide();
      $('#create_workflow_form_container').hide();
      $('#conversation_view').show();
    });
    $tableBody.append($row);
  }
}
