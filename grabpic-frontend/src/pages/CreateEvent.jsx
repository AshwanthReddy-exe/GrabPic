import { useState } from "react";
import { createEvent, uploadImages } from "../api/client";
import { motion, AnimatePresence } from "framer-motion";
import PageWrapper from "../components/PageWrapper";
import RetroButton from "../components/RetroButton";
import DropZone from "../components/DropZone";

const fadeUp = {
  initial: { opacity: 0, y: 16 },
  animate: { opacity: 1, y: 0 },
  exit: { opacity: 0, y: -8 },
  transition: { duration: 0.2, ease: "easeOut" },
};

export default function CreateEvent() {
  const [eventId, setEventId] = useState(null);
  const [files, setFiles] = useState([]);
  const [loading, setLoading] = useState(false);
  const [uploaded, setUploaded] = useState(false);
  const [copied, setCopied] = useState(false);

  const shareLink = eventId
    ? `${window.location.origin}/events/${eventId}`
    : "";

  // Current step (1-based)
  const currentStep = !eventId ? 1 : !uploaded && !loading ? 2 : uploaded ? 4 : 3;

  // ---- HANDLERS ----
  const handleCreateEvent = async () => {
    try {
      setLoading(true);
      const res = await createEvent();
      setEventId(res.data.eventId);
    } catch {
      alert("Failed to create event");
    } finally {
      setLoading(false);
    }
  };

  const handleUpload = async () => {
    if (!files.length) return;
    try {
      setLoading(true);
      const formData = new FormData();
      files.forEach((file) => formData.append("files", file));
      await uploadImages(eventId, formData);
      setUploaded(true);
    } catch {
      alert("Upload failed");
    } finally {
      setLoading(false);
    }
  };

  const copyLink = async () => {
    try {
      await navigator.clipboard.writeText(shareLink);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      // Fallback
      const ta = document.createElement("textarea");
      ta.value = shareLink;
      document.body.appendChild(ta);
      ta.select();
      document.execCommand("copy");
      ta.remove();
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  return (
    <PageWrapper centered>
      <motion.h2
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ duration: 0.2 }}
        style={{
          fontSize: "28px",
          color: "var(--accent-cyan)",
          textShadow: "0 0 16px rgba(0, 255, 224, 0.4)",
          marginBottom: "8px",
        }}
      >
        CREATE EVENT
      </motion.h2>

      {/* Step Indicator */}
      <div className="step-indicator mb-24">
        {[1, 2, 3, 4].map((step, i) => (
          <span key={step}>
            {i > 0 && <span className="step-line" style={{ display: "inline-block", verticalAlign: "middle", marginRight: "12px" }} />}
            <span
              className={`step-dot ${
                step === currentStep
                  ? "step-dot--active"
                  : step < currentStep
                  ? "step-dot--done"
                  : ""
              }`}
              style={{ display: "inline-block", verticalAlign: "middle" }}
            />
          </span>
        ))}
      </div>

      <AnimatePresence mode="wait">
        {/* STEP 1 — Initialize */}
        {currentStep === 1 && (
          <motion.div key="step1" {...fadeUp} className="flex flex-col items-center gap-16">
            <p className="text-muted" style={{ fontSize: "13px", letterSpacing: "0.1em" }}>
              STEP 01 — INITIALIZE EVENT
            </p>
            <RetroButton
              variant="primary"
              onClick={handleCreateEvent}
              disabled={loading}
            >
              {loading ? "Initializing..." : "Create Event"}
            </RetroButton>
          </motion.div>
        )}

        {/* STEP 2 — Upload Photos */}
        {currentStep === 2 && (
          <motion.div key="step2" {...fadeUp} className="card w-full" style={{ maxWidth: "440px" }}>
            <p className="text-muted mb-8" style={{ fontSize: "11px", letterSpacing: "0.1em" }}>
              EVENT ID
            </p>
            <p className="text-cyan mb-16" style={{ fontSize: "13px", wordBreak: "break-all" }}>
              {eventId}
            </p>

            <DropZone
              label="Upload Event Photos"
              sublabel="Drag & drop or click to browse"
              onFiles={(newFiles) => setFiles((prev) => [...prev, ...newFiles])}
              files={files}
              onClear={() => setFiles([])}
              className="mb-16"
            />

            <RetroButton
              variant="primary"
              onClick={handleUpload}
              disabled={!files.length}
              className="w-full"
            >
              Upload & Process
            </RetroButton>
          </motion.div>
        )}

        {/* STEP 3 — Processing */}
        {currentStep === 3 && (
          <motion.div key="step3" {...fadeUp} className="flex flex-col items-center gap-16">
            <div
              style={{
                width: "48px",
                height: "48px",
                border: "2px solid var(--border)",
                borderTop: "2px solid var(--accent-cyan)",
                borderRadius: "50%",
                animation: "spin 1s linear infinite",
              }}
            />
            <p
              className="text-cyan"
              style={{
                fontSize: "14px",
                letterSpacing: "0.15em",
                animation: "text-flicker 2s infinite",
              }}
            >
              Developing film...
            </p>
            <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
          </motion.div>
        )}

        {/* STEP 4 — Share */}
        {currentStep === 4 && (
          <motion.div key="step4" {...fadeUp} className="card w-full" style={{ maxWidth: "440px", textAlign: "center" }}>
            <p
              className="text-cyan mb-16"
              style={{ fontSize: "16px", letterSpacing: "0.15em" }}
            >
              ✓ EVENT READY
            </p>

            <p className="text-muted mb-8" style={{ fontSize: "12px" }}>
              Share this link with attendees:
            </p>

            <div className="copy-row">
              <input
                className="input"
                value={shareLink}
                readOnly
                onClick={(e) => e.target.select()}
              />
              <RetroButton variant="secondary" onClick={copyLink}>
                {copied ? "COPIED ✓" : "COPY"}
              </RetroButton>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </PageWrapper>
  );
}
