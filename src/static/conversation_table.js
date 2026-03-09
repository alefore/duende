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

const conversationTableSorter = new ConversationTableSorter();

function renderConversationsTable(conversationsById) {
  const $div = $('#conversations_table_view');
  $div.empty();

  const $table = $('<table>');
  const $tableBody = $('<tbody>');
  $table.append($tableBody);

  // Create table header
  const $tableHead = $('<thead>');
  const $headerRow = $('<tr>');

  const headers = [
    {text: 'Title', columnId: 'title'},
    {text: 'Messages', columnId: 'messages'},
    {text: 'State', columnId: 'state'},
    {text: 'Last Message', columnId: 'last_message'},
    {text: 'Last Update', columnId: 'last_update'}
  ];

  headers.forEach(header => {
    const $th =
        $('<th>').text(header.text).attr('data-sort-column', header.columnId);
    $th.on('click', function() {
      const columnId = $(this).data('sort-sort-column');
      conversationTableSorter.updateSortState(columnId);
      // TODO: Call sorting function here to re-render/reorder table
      console.log('Sort State:', conversationTableSorter.getSortState());
    });
    $headerRow.append($th);
  });

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
