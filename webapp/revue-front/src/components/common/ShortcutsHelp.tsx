import { WaTooltip } from "../../wa"

export type Shortcut = { keys: string[]; label: string }

/** « ? raccourcis » link, the keyboard shortcuts being listed in its tooltip. */
export function ShortcutsHelp({
  id,
  shortcuts,
}: {
  id: string
  shortcuts: Shortcut[]
}) {
  return (
    <>
      <button id={id} type="button" className="lk shortcuts-link">
        ? raccourcis
      </button>
      <WaTooltip for={id} placement="top-start" className="shortcuts-tooltip">
        <dl className="shortcuts">
          {shortcuts.map(({ keys, label }) => (
            <div key={label} className="shortcuts__item">
              <dt>
                {keys.map((key) => (
                  <kbd key={key}>{key}</kbd>
                ))}
              </dt>
              <dd>{label}</dd>
            </div>
          ))}
        </dl>
      </WaTooltip>
    </>
  )
}
