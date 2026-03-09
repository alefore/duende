function renderConversationsTable(conversationsById) {
  const $tableBody = $('#conversations_table_body');
  $tableBody.empty();

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
      hideConversationsTableView();
    });
    $tableBody.append($row);
  }
}
