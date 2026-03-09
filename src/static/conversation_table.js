import {createTimestampView} from './timestamps.js';

class ConversationTableSorter {
  constructor() {
    this._currentSortColumn = null;
    this._sortDirection = 'asc';  // 'asc' or 'desc'
  }

  getSortState() {
    return {column: this._currentSortColumn, direction: this._sortDirection};
  }

  updateSortState(columnId) {
    if (this._currentSortColumn === columnId) {
      this._sortDirection = (this._sortDirection === 'asc') ? 'desc' : 'asc';
    } else {
      this._currentSortColumn = columnId;
      this._sortDirection = 'asc';
    }
  }
}

function renderConversationsTable(conversationsById) {
  const $div = $('#conversations_table_view');
  $div.empty();

  const $table = $('<table>');
  const $tableBody = $('<tbody>');
  $table.append($tableBody);

  // Create table header
  const $tableHead = $('<thead>');
  const $headerRow = $('<tr>');
  $headerRow.append($('<th>').text('Title'));
  $headerRow.append($('<th>').text('Messages'));
  $headerRow.append($('<th>').text('State'));
  $headerRow.append($('<th>').text('Last Message'));
  $headerRow.append($('<th>').text('Last Update'));
  $tableHead.append($headerRow);
  $table.prepend($tableHead);

  $div.append($table);

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

    // Time Since Last Update
    const $timeSinceLastUpdateTd = $('<td>');
    $timeSinceLastUpdateTd.append(
        createTimestampView(conversation.lastStateChangeTime));
    $row.append($timeSinceLastUpdateTd);

    $row.on('click', function() {
      conversation.show();
      $('#conversations_table_view').hide();
      $('#create_workflow_form_container').hide();
      $('#conversation_view').show();
    });
    $tableBody.append($row);
  }
}
