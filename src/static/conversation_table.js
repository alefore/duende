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

function sortConversations(conversationsById, sortState) {
  const conversationsArray = Object.values(conversationsById);
  const {column, direction} = sortState;

  if (!column) {
    return conversationsArray;
  }

  conversationsArray.sort((a, b) => {
    let valA, valB;

    switch (column) {
      case 'title':
        valA = a.name.toLowerCase();
        valB = b.name.toLowerCase();
        break;
      case 'messages':
        valA = a.countMessages();
        valB = b.countMessages();
        break;
      case 'state':
        valA = a.state.toLowerCase();
        valB = b.state.toLowerCase();
        break;
      case 'last_message':
        valA = a.getLastMessageOverview().toLowerCase();
        valB = b.getLastMessageOverview().toLowerCase();
        break;
      case 'last_update':
        valA = a.lastStateChangeTime;
        valB = b.lastStateChangeTime;
        break;
      default:
        return 0;
    }

    if (valA < valB) {
      return direction === 'asc' ? -1 : 1;
    } else if (valA > valB) {
      return direction === 'asc' ? 1 : -1;
    } else {
      return 0;
    }
  });

  return conversationsArray;
}

function sortAndRenderConversationsTable(conversationsById) {
  const sortedConversations = sortConversations(
      conversationsById, conversationTableSorter.getSortState());

  const $table = $('#conversations_table_view_table');
  $table.empty();

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

  const currentSortState = conversationTableSorter.getSortState();

  headers.forEach(header => {
    const $th = $('<th>').text(header.text);
    if (currentSortState.column === header.columnId) {
      $th.addClass('sort-active');
      $th.addClass(`sort-${currentSortState.direction}`);
    }
    $th.on('click', () => {
      conversationTableSorter.updateSortState(header.columnId);
      sortAndRenderConversationsTable(conversationsById);
    });
    $headerRow.append($th);
  });

  $tableHead.append($headerRow);
  $table.prepend($tableHead);

  sortedConversations.forEach(conversation => {
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
  });
}

// Export the new main rendering function
export {
  sortAndRenderConversationsTable as renderConversationsTable,
  ConversationTableSorter,
  sortConversations
};
