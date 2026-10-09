import WaCallout from "@awesome.me/webawesome/dist/react/callout/index.js"
import WaIcon from "@awesome.me/webawesome/dist/react/icon/index.js"
import { createContext, useCallback, useContext, useState, type ReactNode } from "react"

/** Only errors are notified: successful actions show directly in the table. */
type ErrorItem = { id: number; message: string }

const ErrorContext = createContext<(message: string) => void>(() => {})

export function useNotifyError() {
  return useContext(ErrorContext)
}

let nextId = 0

export function ErrorToaster({ children }: { children: ReactNode }) {
  const [errors, setErrors] = useState<ErrorItem[]>([])
  const notify = useCallback((message: string) => {
    const id = nextId++
    setErrors((current) => [...current, { id, message }])
    window.setTimeout(
      () => setErrors((current) => current.filter((error) => error.id !== id)),
      8000,
    )
  }, [])
  const dismiss = (id: number) =>
    setErrors((current) => current.filter((error) => error.id !== id))

  return (
    <ErrorContext.Provider value={notify}>
      {children}
      <div className="error-toaster" role="alert" aria-live="assertive">
        {errors.map((error) => (
          <WaCallout key={error.id} variant="danger" size="small">
            <WaIcon slot="icon" name="error-warning" />
            <span>{error.message}</span>
            <button
              type="button"
              className="error-toaster__close"
              aria-label="Fermer"
              onClick={() => dismiss(error.id)}
            >
              <WaIcon name="close" />
            </button>
          </WaCallout>
        ))}
      </div>
    </ErrorContext.Provider>
  )
}
