const Icon = (props) => {
  const { entityKey, contentState } = props
  const data = contentState.getEntity(entityKey).getData()
  const src =
    "https://s3.fr-par.scw.cloud/qfdmo-interface/images/364.original.svg?X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Credential=SCWZB4T14FAQ8K9SHDEK%2F20251021%2Ffr-par%2Fs3%2Faws4_request&X-Amz-Date=20251021T154802Z&X-Amz-Expires=3600&X-Amz-SignedHeaders=host&X-Amz-Signature=9f9f7f4df7bdb86e82a5b32aff32edf6b8d9fd9edc48703d8f29c28a3922647f"
  console.log({ props })

  return window.React.createElement("img", {
    src,
    height: "17px",
    width: "auto",
  })
}
class IconSource extends window.React.Component {
  componentDidMount() {
    const { editorState, entityType, onComplete } = this.props

    const content = editorState.getCurrentContent()
    const selection = editorState.getSelection()

    // Uses the Draft.js API to create a new entity with the right data.
    const contentWithEntity = content.createEntity(entityType.type, "IMMUTABLE", {
      icon: "https://s3.fr-par.scw.cloud/qfdmo-interface/images/364.original.svg?X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Credential=SCWZB4T14FAQ8K9SHDEK%2F20251021%2Ffr-par%2Fs3%2Faws4_request&X-Amz-Date=20251021T154802Z&X-Amz-Expires=3600&X-Amz-SignedHeaders=host&X-Amz-Signature=9f9f7f4df7bdb86e82a5b32aff32edf6b8d9fd9edc48703d8f29c28a3922647f",
    })
    const entityKey = contentWithEntity.getLastCreatedEntityKey()

    // console.log(content)

    // // We also add some text for the entity to be activated on.
    const text = `coucou`

    const newContent = window.DraftJS.Modifier.replaceText(
      content,
      selection,
      text,
      null,
      entityKey,
    )
    const nextState = window.DraftJS.EditorState.push(
      editorState,
      newContent,
      "insert-characters",
    )

    onComplete(nextState)
  }

  render() {
    return null
  }
}
// Register the plugin directly on script execution so the editor loads it when initializing.
window.draftail.registerPlugin(
  {
    type: "ICON",
    source: IconSource,
    decorator: Icon,
  },
  "entityTypes",
)
