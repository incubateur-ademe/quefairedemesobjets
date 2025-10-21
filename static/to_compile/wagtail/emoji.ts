import "./emoji.css"
;(function () {
  window.draftail.registerPlugin({
    type: "EMOJI",
    source: null,
    decorator: null,
    block: false,
    inline: true,
    entityType: "EMOJI",
    control: {
      type: "emoji",
      icon: "😊",
      description: "Insert emoji",
      onClick: (event, { editorState, onChange }) => {
        const emoji = prompt("Enter emoji (e.g. 😀):")
        if (emoji) {
          const selection = editorState.getSelection()
          const contentState = editorState.getCurrentContent()
          const newContent = Draft.Modifier.insertText(contentState, selection, emoji)
          const newState = Draft.EditorState.push(
            editorState,
            newContent,
            "insert-characters",
          )
          onChange(newState)
        }
      },
    },
  })
})()
