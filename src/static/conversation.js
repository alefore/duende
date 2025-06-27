let shownConversationId = null;

class ConversationData {
  constructor(id, name, state, stateEmoji) {
    this.id = id;
    this.name = name;
    this.state = state;
    this.stateEmoji = stateEmoji;

    console.log(`Creating container for conversation ${this.id}`);
    this.div = $('<div>')
                   .addClass('conversation')
                   .attr('id', `conversation-${id}`)
                   .hide();
    $('#conversation_container').append(this.div);
  }

  isShown() {
    return this.id === shownConversationId;
  }

  show() {
    $('.conversation').hide();  // Hide all.
    shownConversationId = this.id;
    this.div.show();
    const $conversationSelector = $('#conversation_selector');
    if (parseInt($conversationSelector.val()) !== this.id)
      $conversationSelector.val(this.id);
    this._updateShownConversationState();
    scrollToBottom();
  }

  updateData(name, state, stateEmoji) {
    this.name = name;
    this.state = state;
    this.stateEmoji = stateEmoji;
  }

  updateView() {
    this._updateSelectorOption();
    if (shownConversationId === null)
      this.show();
    else if (this.isShown())
      this._updateShownConversationState();
    return this;
  }

  isWaitingForConfirmation() {
    return this.state === 'WAITING_FOR_CONFIRMATION';
  }

  countMessages() {
    return this.div.find('.message').length;
  }

  addMessage(message) {
    console.log(message);
    const $messageDiv = $('<div>').addClass('message');
    const $role = $('<p>').addClass('role').text(`${message.role}:`);

    const creationTimestamp = new Date(message.creation_time).getTime();
    const $timestampView = createTimestampView(creationTimestamp);
    $timestampView.addClass('timestamp');

    const $messageHeader = $('<div>').addClass('message-header');
    $messageHeader.append($role, $timestampView);

    const $contentContainer = $('<div>').addClass('content-container');
    (message.content_sections || []).forEach(section => {
      const $sectionDiv = $('<div>').addClass('messageSection');
      const lineCount = section.content.length;
      const $fullContentPre = $('<pre>')
                                  .addClass('full-content-pre')
                                  .text(section.content.join('\n'));

      if (lineCount <= 5) {
        $sectionDiv.append($fullContentPre);
      } else {
        const firstLineContent = section.summary || section.content[0] || '';
        const $firstLinePre =
            $('<pre>')
                .addClass('first-line-pre')
                .text(
                    firstLineContent.length > 100 ?
                        firstLineContent.substring(0, 100) + '...' :
                        firstLineContent);

        const $sectionHeader = $('<div>').addClass('section-header');
        const $expandLink =
            $('<span>').addClass('toggle-link expand').text('[expand]');
        const $collapseLink = $('<span>')
                                  .addClass('toggle-link collapse')
                                  .text('[collapse]')
                                  .hide();
        const $lineCountSpan =
            $('<span>').addClass('line-count').text(` (${lineCount} lines)`);

        $sectionHeader.append($expandLink, $collapseLink, $lineCountSpan);
        $sectionDiv.append($sectionHeader, $firstLinePre, $fullContentPre);

        $expandLink.on('click', () => {
          $fullContentPre.show();
          $firstLinePre.hide();
          $expandLink.hide();
          $lineCountSpan.hide();
          $collapseLink.show();
        });

        $collapseLink.on('click', () => {
          $fullContentPre.hide();
          $firstLinePre.show();
          $expandLink.show();
          $lineCountSpan.show();
          $collapseLink.hide();
        });
        $collapseLink.click();
      }
      $contentContainer.append($sectionDiv);
    });

    this.div.append($messageDiv.append($messageHeader, $contentContainer));
  }

  _updateSelectorOption() {
    const $conversationSelector = $('#conversation_selector');
    let $option = $conversationSelector.find(`option[value="${this.id}"]`);
    if ($option.length === 0) {
      $option = $('<option>').val(this.id);
      $conversationSelector.append($option);
    }
    $option.text(`${this.name} (${this.countMessages()}, ${this.stateEmoji})`);
  }

  _updateShownConversationState() {
    const $confirmationForm = $('#confirmation_form');
    const $confirmationInput = $('#confirmation_input');
    const $stateDisplay = $('#conversation_state_display');

    // Default to hiding both elements
    $confirmationForm.hide();
    $stateDisplay.hide();

    if (this.isWaitingForConfirmation()) {
      $confirmationForm.show();
      $confirmationInput.focus();
    } else if (this.state) {
      $confirmationInput.val('');
      const prettyState = this.state.replace(/_/g, ' ').toLowerCase();
      $stateDisplay
          .text(
              this.stateEmoji + ' ' + prettyState.charAt(0).toUpperCase() +
              prettyState.slice(1))
          .show();
    }
  }
}
