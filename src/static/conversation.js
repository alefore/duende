let shownConversationId = null;

class ConversationData {
  constructor(id, name, state, stateEmoji, lastStateChangeTime) {
    this.id = id;
    this.name = name;
    this.state = state;
    this.stateEmoji = stateEmoji;
    this.lastStateChangeTime = lastStateChangeTime;  // Fixed typo here
    // This is not the time at which it was sent; rather, it is the value of
    // lastStateChangeTime when the confirmation was sent (which is good enough
    // to make sure we don't send multiple confirmations for the same request).
    this.lastConfirmationSentTime = null;

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
  }

  updateData(name, state, stateEmoji, lastStateChangeTime) {
    this.name = name;
    this.state = state;
    this.stateEmoji = stateEmoji;
    this.lastStateChangeTime = lastStateChangeTime;
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
    return this.state === 'WAITING_FOR_CONFIRMATION' &&
        (this.lastConfirmationSentTime === null ||
         this.lastConfirmationSentTime < this.lastStateChangeTime);
  }

  notifyConfirmationSent() {
    this.lastConfirmationSentTime = this.lastStateChangeTime;
    return this;
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

    const $messageHeader = $('<div>').addClass('message-header');
    $messageHeader.append($role, $timestampView);

    const $contentContainer = $('<div>').addClass('content-container');
    (message.content_sections || []).forEach(section => {
      const $sectionDiv = $('<div>').addClass('messageSection');

      // Returns a jQuery object containing the elements for collapsible content
      const createCollapsibleContent = (content, summaryContent) => {
        if (content === undefined || content === null || content === '')
          return null;

        const lineCount = String(content).split('\n').length;
        const $contentPre =
            $('<pre>').addClass('field-content-pre').text(content);
        const $container = $('<div>').addClass('collapsible-content-container');

        if (lineCount > 5) {
          const $summaryPre = $('<pre>').addClass('field-summary-pre');
          const summary = summaryContent ||
              String(content).split('\n').slice(0, 5).join('\n') + '...';
          $summaryPre.text(summary);

          const $toggleLink =
              $('<span>').addClass('toggle-link').text('[expand]');
          const $lineCountSpan =
              $('<span>').addClass('line-count').text(` (${lineCount} lines)`);

          const $header = $('<div>').addClass('field-header');
          $header.append($toggleLink, $lineCountSpan);

          $toggleLink.on('click', () => {
            if ($contentPre.is(':visible')) {
              $contentPre.hide();
              $summaryPre.show();
              $toggleLink.text('[expand]');
            } else {
              $contentPre.show();
              $summaryPre.hide();
              $toggleLink.text('[collapse]');
            }
          });
          $toggleLink.click();  // Initialize in collapsed state

          $container.append($header, $summaryPre, $contentPre);
        } else {
          $container.append($contentPre);
        }
        return $container;
      };

      const renderPropertiesTable = (propertiesObject, orderedKeys, title) => {
        const $block = $('<div>').addClass(
            title.toLowerCase().replace(/ /g, '-') + '-block');
        $block.append($('<h3>').html(title));
        const $table = $('<table>').addClass('properties-table');

        orderedKeys.forEach(key => {
          const value = propertiesObject[key];
          const displayLabel =
              key.replace(/_/g, ' ')
                  .split(' ')
                  .map(word => word.charAt(0).toUpperCase() + word.slice(1))
                  .join(' ');

          const $collapsibleContent = createCollapsibleContent(value);
          if ($collapsibleContent) {
            const $row = $('<tr>');
            $row.append(
                $('<td>').addClass('property-label').text(`${displayLabel}:`));
            $row.append($('<td>')
                            .addClass('property-value')
                            .append($collapsibleContent));
            $table.append($row);
          }
        });
        $block.append($table);
        return $block;
      };

      if (section.command) {
        const commandKeys = Object.keys(section.command)
                                .filter(key => key !== 'command_name')
                                .sort();
        const orderedCommandKeys = ['command_name', ...commandKeys];
        const $commandBlock = renderPropertiesTable(
            section.command, orderedCommandKeys, '&#129302; Command');
        $sectionDiv.append($commandBlock);
      } else if (section.command_output) {
        const outputKeys =
            ['command_name', 'output', 'errors', 'summary', 'task_done'];
        const $outputBlock = renderPropertiesTable(
            section.command_output, outputKeys,
            '&#9881;&#65039; Command Output');
        $sectionDiv.append($outputBlock);
      } else if (section.content && section.content.length > 0) {
        const $contentElement =
            createCollapsibleContent(section.content, section.summary);
        if ($contentElement) {
          $sectionDiv.append($contentElement);
        }
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
      const stateText = this.stateEmoji + ' ' +
          prettyState.charAt(0).toUpperCase() + prettyState.slice(1);
      $stateDisplay.empty()
          .append(stateText)
          .append(' ')
          .append(createTimestampView(this.lastStateChangeTime))
          .show();
    }
    scrollToBottom();
  }
}