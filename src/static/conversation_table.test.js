import { ConversationTableSorter, sortConversations } from './conversation_table.js';

function assert(condition, message) {
  if (!condition) {
    throw new Error(message || 'Assertion failed');
  }
}

// Mock Conversation object for testing sortConversations
class MockConversation {
  constructor(id, name, messagesCount, state, lastMessageOverview, lastStateChangeTime) {
    this.id = id;
    this.name = name;
    this._messagesCount = messagesCount;
    this.state = state;
    this._lastMessageOverview = lastMessageOverview;
    this.lastStateChangeTime = lastStateChangeTime;
  }

  countMessages() {
    return this._messagesCount;
  }

  getLastMessageOverview() {
    return this._lastMessageOverview;
  }
}

function runConversationTableSorterTests() {
  console.log('Running ConversationTableSorter Unit Tests...');

  // Test 1: Initial state
  const sorter1 = new ConversationTableSorter();
  let state1 = sorter1.getSortState();
  assert(state1.column === null, 'Test 1.1 Failed: Initial column should be null');
  assert(state1.direction === 'asc', 'Test 1.2 Failed: Initial direction should be asc');
  console.log('Test 1 Passed: Initial state is correct.');

  // Test 2: Update sort state for a new column
  sorter1.updateSortState('title');
  state1 = sorter1.getSortState();
  assert(state1.column === 'title', 'Test 2.1 Failed: Column should be title');
  assert(state1.direction === 'asc', 'Test 2.2 Failed: Direction should be asc for new column');
  console.log('Test 2 Passed: New column sort state updated correctly.');

  // Test 3: Toggle sort direction for the same column
  sorter1.updateSortState('title');
  state1 = sorter1.getSortState();
  assert(state1.column === 'title', 'Test 3.1 Failed: Column should still be title');
  assert(state1.direction === 'desc', 'Test 3.2 Failed: Direction should be desc after toggling');
  console.log('Test 3 Passed: Toggle sort direction works.');

  // Test 4: Update sort state to another new column
  sorter1.updateSortState('messages');
  state1 = sorter1.getSortState();
  assert(state1.column === 'messages', 'Test 4.1 Failed: Column should be messages');
  assert(state1.direction === 'asc', 'Test 4.2 Failed: Direction should be asc for new column');
  console.log('Test 4 Passed: Another new column sort state updated correctly.');

  console.log('All ConversationTableSorter Unit Tests Passed!');
}

function runSortConversationsTests() {
  console.log('Running sortConversations Unit Tests...');

  const mockConversations = {
    'conv1': new MockConversation('conv1', 'Conversation B', 5, 'active', 'last message B', 1678886400000), // March 15, 2023 12:00:00 PM GMT
    'conv2': new MockConversation('conv2', 'Conversation A', 10, 'pending', 'last message A', 1678972800000), // March 16, 2023 12:00:00 PM GMT
    'conv3': new MockConversation('conv3', 'Conversation C', 2, 'done', 'last message C', 1678799900000), // March 14, 2023 11:58:20 PM GMT
  };

  // Test 1: Sort by title ascending
  let sorted = sortConversations(mockConversations, { column: 'title', direction: 'asc' });
  assert(sorted[0].name === 'Conversation A', 'Test 1.1 Failed: Sort by title asc (1)');
  assert(sorted[1].name === 'Conversation B', 'Test 1.2 Failed: Sort by title asc (2)');
  assert(sorted[2].name === 'Conversation C', 'Test 1.3 Failed: Sort by title asc (3)');
  console.log('Test 1 Passed: Sort by title ascending works.');

  // Test 2: Sort by title descending
  sorted = sortConversations(mockConversations, { column: 'title', direction: 'desc' });
  assert(sorted[0].name === 'Conversation C', 'Test 2.1 Failed: Sort by title desc (1)');
  assert(sorted[1].name === 'Conversation B', 'Test 2.2 Failed: Sort by title desc (2)');
  assert(sorted[2].name === 'Conversation A', 'Test 2.3 Failed: Sort by title desc (3)');
  console.log('Test 2 Passed: Sort by title descending works.');

  // Test 3: Sort by messages ascending
  sorted = sortConversations(mockConversations, { column: 'messages', direction: 'asc' });
  assert(sorted[0].name === 'Conversation C', 'Test 3.1 Failed: Sort by messages asc (1)');
  assert(sorted[1].name === 'Conversation B', 'Test 3.2 Failed: Sort by messages asc (2)');
  assert(sorted[2].name === 'Conversation A', 'Test 3.3 Failed: Sort by messages asc (3)');
  console.log('Test 3 Passed: Sort by messages ascending works.');

  // Test 4: Sort by messages descending
  sorted = sortConversations(mockConversations, { column: 'messages', direction: 'desc' });
  assert(sorted[0].name === 'Conversation A', 'Test 4.1 Failed: Sort by messages desc (1)');
  assert(sorted[1].name === 'Conversation B', 'Test 4.2 Failed: Sort by messages desc (2)');
  assert(sorted[2].name === 'Conversation C', 'Test 4.3 Failed: Sort by messages desc (3)');
  console.log('Test 4 Passed: Sort by messages descending works.');

  // Test 5: Sort by state ascending
  sorted = sortConversations(mockConversations, { column: 'state', direction: 'asc' });
  assert(sorted[0].name === 'Conversation B', 'Test 5.1 Failed: Sort by state asc (1)'); // active
  assert(sorted[1].name === 'Conversation C', 'Test 5.2 Failed: Sort by state asc (2)'); // done
  assert(sorted[2].name === 'Conversation A', 'Test 5.3 Failed: Sort by state asc (3)'); // pending
  console.log('Test 5 Passed: Sort by state ascending works.');

  // Test 6: Sort by state descending
  sorted = sortConversations(mockConversations, { column: 'state', direction: 'desc' });
  assert(sorted[0].name === 'Conversation A', 'Test 6.1 Failed: Sort by state desc (1)'); // pending
  assert(sorted[1].name === 'Conversation C', 'Test 6.2 Failed: Sort by state desc (2)'); // done
  assert(sorted[2].name === 'Conversation B', 'Test 6.3 Failed: Sort by state desc (3)'); // active
  console.log('Test 6 Passed: Sort by state descending works.');

  // Test 7: Sort by last_message ascending
  sorted = sortConversations(mockConversations, { column: 'last_message', direction: 'asc' });
  assert(sorted[0].name === 'Conversation A', 'Test 7.1 Failed: Sort by last_message asc (1)');
  assert(sorted[1].name === 'Conversation B', 'Test 7.2 Failed: Sort by last_message asc (2)');
  assert(sorted[2].name === 'Conversation C', 'Test 7.3 Failed: Sort by last_message asc (3)');
  console.log('Test 7 Passed: Sort by last_message ascending works.');

  // Test 8: Sort by last_message descending
  sorted = sortConversations(mockConversations, { column: 'last_message', direction: 'desc' });
  assert(sorted[0].name === 'Conversation C', 'Test 8.1 Failed: Sort by last_message desc (1)');
  assert(sorted[1].name === 'Conversation B', 'Test 8.2 Failed: Sort by last_message desc (2)');
  assert(sorted[2].name === 'Conversation A', 'Test 8.3 Failed: Sort by last_message desc (3)');
  console.log('Test 8 Passed: Sort by last_message descending works.');

  // Test 9: Sort by last_update ascending
  sorted = sortConversations(mockConversations, { column: 'last_update', direction: 'asc' });
  assert(sorted[0].name === 'Conversation C', 'Test 9.1 Failed: Sort by last_update asc (1)'); // earliest timestamp
  assert(sorted[1].name === 'Conversation B', 'Test 9.2 Failed: Sort by last_update asc (2)');
  assert(sorted[2].name === 'Conversation A', 'Test 9.3 Failed: Sort by last_update asc (3)'); // latest timestamp
  console.log('Test 9 Passed: Sort by last_update ascending works.');

  // Test 10: Sort by last_update descending
  sorted = sortConversations(mockConversations, { column: 'last_update', direction: 'desc' });
  assert(sorted[0].name === 'Conversation A', 'Test 10.1 Failed: Sort by last_update desc (1)'); // latest timestamp
  assert(sorted[1].name === 'Conversation B', 'Test 10.2 Failed: Sort by last_update desc (2)');
  assert(sorted[2].name === 'Conversation C', 'Test 10.3 Failed: Sort by last_update desc (3)'); // earliest timestamp
  console.log('Test 10 Passed: Sort by last_update descending works.');

  // Test 11: No sort column specified, should return original order (or no change)
  const originalOrder = Object.values(mockConversations);
  sorted = sortConversations(mockConversations, { column: null, direction: 'asc' });
  assert(JSON.stringify(sorted) === JSON.stringify(originalOrder), 'Test 11 Failed: No sort column should return original order');
  console.log('Test 11 Passed: No sort column returns original order.');

  console.log('All sortConversations Unit Tests Passed!');
}

// Run all tests
try {
  runConversationTableSorterTests();
  runSortConversationsTests();
  console.log('All Unit Tests Completed Successfully!');
} catch (error) {
  console.error('Unit Tests Failed:', error.message);
  console.error(error.stack);
}
