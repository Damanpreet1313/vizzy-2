import { useState, useEffect, useCallback } from 'react'
import styles from './ReaderMode.module.css'

export default function ReaderMode({ collection, startIndex = 0, onClose }) {
  const [index, setIndex] = useState(startIndex)
  const [imgLoaded, setImgLoaded] = useState(false)

  const frame = collection[index]
  const isFirst = index === 0
  const isLast = index === collection.length - 1

  const goNext = useCallback(() => {
    if (!isLast) {
      setImgLoaded(false)
      setIndex((i) => i + 1)
    }
  }, [isLast])

  const goPrev = useCallback(() => {
    if (!isFirst) {
      setImgLoaded(false)
      setIndex((i) => i - 1)
    }
  }, [isFirst])

  // Keyboard navigation
  useEffect(() => {
    function onKey(e) {
      if (e.key === 'ArrowRight' || e.key === 'ArrowDown' || e.key === ' ') {
        e.preventDefault()
        goNext()
      }
      if (e.key === 'ArrowLeft' || e.key === 'ArrowUp') {
        e.preventDefault()
        goPrev()
      }
      if (e.key === 'Escape') onClose()
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [goNext, goPrev, onClose])

  // Prevent body scroll while reader is open
  useEffect(() => {
    document.body.style.overflow = 'hidden'
    return () => { document.body.style.overflow = '' }
  }, [])

  return (
    <div className={styles.overlay}>
      {/* Top bar */}
      <div className={styles.topBar}>
        <div className={styles.progress}>
          {collection.map((_, i) => (
            <button
              key={i}
              className={`${styles.dot} ${i === index ? styles.dotActive : i < index ? styles.dotDone : ''}`}
              onClick={() => { setImgLoaded(false); setIndex(i) }}
              aria-label={`Go to frame ${i + 1}`}
            />
          ))}
        </div>
        <span className={styles.counter}>{index + 1} / {collection.length}</span>
        <button className={styles.closeBtn} onClick={onClose} aria-label="Close reader">✕</button>
      </div>

      {/* Main image */}
      <div className={styles.imageArea}>
        {!imgLoaded && (
          <div className={styles.imgPlaceholder}>
            <span className={styles.imgSpinner} />
          </div>
        )}
        <img
          key={frame.image_url}
          src={frame.image_url}
          alt={`Frame ${index + 1}`}
          className={`${styles.image} ${imgLoaded ? styles.imageVisible : ''}`}
          onLoad={() => setImgLoaded(true)}
        />
      </div>

      {/* Info panel */}
      <div className={styles.infoPanel}>
        <div className={styles.infoInner}>
          {frame.quote && (
            <blockquote className={styles.quote}>
              <span className={styles.quoteMark}>"</span>
              {frame.quote}
              <span className={styles.quoteMark}>"</span>
            </blockquote>
          )}
          {frame.text_summary && (
            <p className={styles.summary}>{frame.text_summary}</p>
          )}
        </div>

        {/* Navigation */}
        <div className={styles.navRow}>
          <button
            className={`${styles.navBtn} ${styles.prevBtn}`}
            onClick={goPrev}
            disabled={isFirst}
            aria-label="Previous frame"
          >
            ← Prev
          </button>

          <div className={styles.navHint}>
            <span>← → arrow keys</span>
            <span>·</span>
            <span>Space to advance</span>
          </div>

          <button
            className={`${styles.navBtn} ${styles.nextBtn} ${isLast ? styles.finishBtn : ''}`}
            onClick={isLast ? onClose : goNext}
            aria-label={isLast ? 'Finish reading' : 'Next frame'}
          >
            {isLast ? 'Finish ✦' : 'Next →'}
          </button>
        </div>
      </div>
    </div>
  )
}
