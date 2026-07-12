import { useEffect, useRef, useState, type ReactNode } from 'react'

export interface ParamInfo {
  title: string
  body: string
  illustration?: ReactNode
}

/** Small "i" button that toggles an explanatory popover next to a form
 *  label: a plain-language description of the parameter and, where it
 *  helps, a small inline SVG illustration (no external assets). */
type Alignment = 'center' | 'align-left' | 'align-right'

function InfoTip({ info }: { info: ParamInfo }) {
  const [open, setOpen] = useState(false)
  const [alignment, setAlignment] = useState<Alignment>('center')
  const rootRef = useRef<HTMLSpanElement>(null)

  useEffect(() => {
    if (!open) return
    function onPointerDown(event: PointerEvent) {
      if (rootRef.current && !rootRef.current.contains(event.target as Node)) {
        setOpen(false)
      }
    }
    function onKeyDown(event: KeyboardEvent) {
      if (event.key === 'Escape') setOpen(false)
    }
    document.addEventListener('pointerdown', onPointerDown)
    document.addEventListener('keydown', onKeyDown)
    return () => {
      document.removeEventListener('pointerdown', onPointerDown)
      document.removeEventListener('keydown', onKeyDown)
    }
  }, [open])

  return (
    <span className="infotip" ref={rootRef}>
      <button
        type="button"
        className="infotip-button"
        aria-label={`What is "${info.title}"?`}
        aria-expanded={open}
        onClick={(event) => {
          // Inside a <label>: stop the click from focusing the input.
          event.preventDefault()
          event.stopPropagation()
          const rect = event.currentTarget.getBoundingClientRect()
          const popoverHalfWidth = 140
          if (rect.left < popoverHalfWidth) setAlignment('align-left')
          else if (window.innerWidth - rect.right < popoverHalfWidth) setAlignment('align-right')
          else setAlignment('center')
          setOpen((prev) => !prev)
        }}
      >
        i
      </button>
      {open && (
        <span
          className={`infotip-popover${alignment === 'center' ? '' : ` ${alignment}`}`}
          role="note"
        >
          <strong className="infotip-title">{info.title}</strong>
          <span className="infotip-body">{info.body}</span>
          {info.illustration && (
            <span className="infotip-figure" aria-hidden="true">
              {info.illustration}
            </span>
          )}
        </span>
      )}
    </span>
  )
}

export default InfoTip
