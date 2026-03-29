import { useEffect, useCallback } from "react";
import { motion, AnimatePresence } from "framer-motion";
import RetroButton from "./RetroButton";

/**
 * ImageModal — Fullscreen lightbox with keyboard navigation.
 */
export default function ImageModal({
  images = [],
  selectedIndex,
  onClose,
  onNavigate,
  getImageSrc,
  getDownloadHref,
}) {
  const isOpen = selectedIndex !== null && selectedIndex !== undefined;
  const currentImage = isOpen ? images[selectedIndex] : null;

  const goLeft = useCallback(() => {
    if (selectedIndex > 0) onNavigate(selectedIndex - 1);
  }, [selectedIndex, onNavigate]);

  const goRight = useCallback(() => {
    if (selectedIndex < images.length - 1) onNavigate(selectedIndex + 1);
  }, [selectedIndex, images.length, onNavigate]);

  useEffect(() => {
    if (!isOpen) return;

    const handler = (e) => {
      if (e.key === "Escape") onClose();
      if (e.key === "ArrowLeft") goLeft();
      if (e.key === "ArrowRight") goRight();
    };

    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, [isOpen, goLeft, goRight, onClose]);

  // Lock body scroll when modal is open
  useEffect(() => {
    if (isOpen) {
      document.body.style.overflow = "hidden";
    } else {
      document.body.style.overflow = "";
    }
    return () => {
      document.body.style.overflow = "";
    };
  }, [isOpen]);

  return (
    <AnimatePresence>
      {isOpen && currentImage && (
        <motion.div
          className="modal-overlay"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          transition={{ duration: 0.15 }}
          onClick={onClose}
        >
          <motion.div
            className="modal-content"
            initial={{ scale: 0.9, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            exit={{ scale: 0.9, opacity: 0 }}
            transition={{ duration: 0.18, ease: "easeOut" }}
            onClick={(e) => e.stopPropagation()}
          >
            {/* Close */}
            <RetroButton
              variant="icon"
              className="modal-close"
              onClick={onClose}
              aria-label="Close"
            >
              ✕
            </RetroButton>

            {/* Nav Left */}
            {selectedIndex > 0 && (
              <RetroButton
                variant="icon"
                className="modal-nav modal-nav--left"
                onClick={goLeft}
                aria-label="Previous image"
              >
                ◀
              </RetroButton>
            )}

            {/* Image */}
            <img
              src={getImageSrc(currentImage)}
              alt={`Photo ${selectedIndex + 1}`}
              className="modal-image"
            />

            {/* Nav Right */}
            {selectedIndex < images.length - 1 && (
              <RetroButton
                variant="icon"
                className="modal-nav modal-nav--right"
                onClick={goRight}
                aria-label="Next image"
              >
                ▶
              </RetroButton>
            )}

            {/* Actions */}
            <div className="modal-actions">
              <a
                href={getDownloadHref(currentImage)}
                download
                className="btn btn--primary"
              >
                ↓ DOWNLOAD
              </a>
            </div>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
