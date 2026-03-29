import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { motion } from "framer-motion";
import PageWrapper from "../components/PageWrapper";
import RetroButton from "../components/RetroButton";

const stagger = {
  animate: { transition: { staggerChildren: 0.08 } },
};

const fadeUp = {
  initial: { opacity: 0, y: 20 },
  animate: { opacity: 1, y: 0 },
};

export default function Home() {
  const navigate = useNavigate();
  const [eventId, setEventId] = useState("");

  const handleOpenEvent = () => {
    const id = eventId.trim();
    if (id) navigate(`/events/${id}`);
  };

  const handleKeyDown = (e) => {
    if (e.key === "Enter") handleOpenEvent();
  };

  return (
    <PageWrapper centered>
      <motion.div
        variants={stagger}
        initial="initial"
        animate="animate"
        className="flex flex-col items-center"
        style={{ gap: "24px", textAlign: "center" }}
      >
        {/* Title */}
        <motion.h1
          variants={fadeUp}
          transition={{ duration: 0.25 }}
          style={{
            fontSize: "clamp(48px, 10vw, 80px)",
            color: "var(--accent-cyan)",
            textShadow: "0 0 30px rgba(0, 255, 224, 0.5), 0 0 60px rgba(0, 255, 224, 0.2)",
            letterSpacing: "0.25em",
            animation: "text-flicker 4s infinite",
          }}
        >
          GRABPIC
        </motion.h1>

        {/* Subtitle */}
        <motion.p
          variants={fadeUp}
          transition={{ duration: 0.25 }}
          style={{
            color: "var(--text-muted)",
            fontSize: "14px",
            letterSpacing: "0.3em",
            textTransform: "uppercase",
          }}
        >
          find yourself in memories
        </motion.p>

        {/* Buttons */}
        <motion.div
          variants={fadeUp}
          transition={{ duration: 0.25 }}
          className="flex items-center"
          style={{ gap: "16px", marginTop: "24px", flexWrap: "wrap", justifyContent: "center" }}
        >
          <RetroButton variant="primary" onClick={() => navigate("/create")}>
            Create Event
          </RetroButton>
        </motion.div>

        {/* Open Event Input */}
        <motion.div
          variants={fadeUp}
          transition={{ duration: 0.25 }}
          style={{ marginTop: "12px", width: "100%", maxWidth: "360px" }}
        >
          <div className="event-id-row">
            <input
              className="input"
              type="text"
              placeholder="Enter Event ID..."
              value={eventId}
              onChange={(e) => setEventId(e.target.value)}
              onKeyDown={handleKeyDown}
            />
            <RetroButton
              variant="secondary"
              onClick={handleOpenEvent}
              disabled={!eventId.trim()}
            >
              GO →
            </RetroButton>
          </div>
        </motion.div>
      </motion.div>
    </PageWrapper>
  );
}
