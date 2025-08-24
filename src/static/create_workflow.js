const socket = io();

function showCreateWorkflowForm() {
  $('#conversation_view').hide();
  $('#create_workflow_form_container').show();
}

function resetAndHideCreateWorkflowForm() {
  $('#create_workflow_form_container').hide();
  $('#conversation_view').show();
  $('#original_task_prompt_content').val('');  // Clear the textarea content.
}

$(document).ready(function() {
  $('#create_workflow_form').submit(function(event) {
    event.preventDefault();  // Prevent default form submission

    const originalTaskPromptContent = $('#original_task_prompt_content').val();

    if (originalTaskPromptContent.trim() === '') {
      alert('Please enter a task prompt.');
      return;
    }

    const data = {
      name: 'implement_and_review',
      args: {original_task_prompt_content: originalTaskPromptContent}
    };

    console.log('Emitting create_agent_workflow:', data);
    socket.emit('create_agent_workflow', data);

    resetAndHideCreateWorkflowForm();
  });

  // Attach click event for the cancel button
  $('#create_workflow_form_container button[type="button"]')
      .on('click', function() {
        resetAndHideCreateWorkflowForm();
      });
});
