function createTimestampView(timestamp) {
  const $element = $('<span>');

  function formatTime(value, unit) {
    if (value === 1) {
      return `1 ${unit} ago`;
    }
    return `${value} ${unit}s ago`;
  }

  function updateText() {
    const nowMs = new Date().getTime();
    const diffSeconds = Math.floor((nowMs - timestamp) / 1000);
    let text;
    let nextUpdateInMs;

    if (diffSeconds < 5) {
      text = 'now';
      nextUpdateInMs = 1000;
    } else if (diffSeconds < 60) {
      text = formatTime(diffSeconds, 'second');
      nextUpdateInMs = 1000;
    } else if (diffSeconds < 3600) {
      const diffMinutes = Math.floor(diffSeconds / 60);
      text = formatTime(diffMinutes, 'minute');
      nextUpdateInMs = 30 * 1000;
    } else if (diffSeconds < 86400) {
      const diffHours = Math.floor(diffSeconds / 3600);
      text = formatTime(diffHours, 'hour');
      nextUpdateInMs = 30 * 60 * 1000;
    } else if (diffSeconds < 86400 * 8) {
      const diffDays = Math.floor(diffSeconds / 86400);
      text = formatTime(diffDays, 'day');
      nextUpdateInMs = 60 * 60 * 1000;
    } else {
      const date = new Date(timestamp);
      const year = date.getFullYear();
      const month = String(date.getMonth() + 1).padStart(2, '0');
      const day = String(date.getDate()).padStart(2, '0');
      text = `${year}-${month}-${day}`;
      nextUpdateInMs = -1;
    }

    $element.text(text);
    // We use 10 seconds to make sure we give JS a chance to add this event to
    // the DOM (when we first create it).
    if (nextUpdateInMs > 10000) {
      setTimeout(() => {
        if ($.contains(document.documentElement, $element[0])) {
          updateText();
        }
      }, nextUpdateInMs);
    }
  }

  updateText();
  return $element;
}
