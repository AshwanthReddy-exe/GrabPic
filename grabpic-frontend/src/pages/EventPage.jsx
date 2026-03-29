import { useParams } from "react-router-dom";
import { useState, useRef, useCallback } from "react";
import { searchImages, getImageUrl, downloadAllImages } from "../api/client";
import { motion } from "framer-motion";
import PageWrapper from "../components/PageWrapper";
import RetroButton from "../components/RetroButton";
import DropZone from "../components/DropZone";
import SkeletonGrid from "../components/SkeletonGrid";
import ImageModal from "../components/ImageModal";

const fadeUp = {
  initial: { opacity: 0, y: 12 },
  animate: { opacity: 1, y: 0 },
  transition: { duration: 0.2 },
};

export default function EventPage() {
  const { eventId } = useParams();

  const [files, setFiles] = useState([]);
  const [images, setImages] = useState({ strong: [], weak: [] });
  const [page, setPage] = useState(1);
  const [hasMore, setHasMore] = useState(false);
  const [loading, setLoading] = useState(false);
  const [selectedIndex, setSelectedIndex] = useState(null);
  const [allImagesFlat, setAllImagesFlat] = useState([]);

  const observerRef = useRef();

  // ---- FILE HANDLER (AUTO SEARCH) ----
  const handleFiles = async (fileList) => {
    if (fileList.length === 0) return;
    if (fileList.length > 4) {
      alert("Max 4 selfies allowed");
      return;
    }

    setFiles(fileList);
    setPage(1);
    setImages({ strong: [], weak: [] });
    setAllImagesFlat([]);

    await performSearch(fileList, 1);
  };

  // ---- SEARCH ----
  const performSearch = async (fileSet, pageNum) => {
    try {
      setLoading(true);
      const formData = new FormData();
      fileSet.forEach((f) => formData.append("files", f));

      const res = await searchImages(eventId, formData, pageNum, 12);
      const strong = res.data.strongMatches;
      const weak = res.data.weakMatches;

      if (pageNum === 1) {
        setImages({ strong, weak });
        setAllImagesFlat([...strong, ...weak]);
      } else {
        setImages((prev) => ({
          strong: [...prev.strong, ...strong],
          weak: [...prev.weak, ...weak],
        }));
        setAllImagesFlat((prev) => [...prev, ...strong, ...weak]);
      }

      setPage(pageNum + 1);
      setHasMore(res.data.hasMore);
    } catch {
      alert("Search failed");
    } finally {
      setLoading(false);
    }
  };

  // ---- LOAD MORE ----
  const loadMore = useCallback(() => {
    if (!hasMore || loading) return;
    performSearch(files, page);
  }, [hasMore, loading, files, page]);

  // ---- INTERSECTION OBSERVER ----
  const lastImageRef = useCallback(
    (node) => {
      if (loading) return;
      if (observerRef.current) observerRef.current.disconnect();

      observerRef.current = new IntersectionObserver((entries) => {
        if (entries[0].isIntersecting) loadMore();
      });

      if (node) observerRef.current.observe(node);
    },
    [loadMore]
  );

  // ---- DOWNLOAD ALL ----
  const downloadAll = () => {
    downloadAllImages(eventId);
  };

  // ---- HELPERS ----
  const hasResults = images.strong.length > 0 || images.weak.length > 0;

  return (
    <PageWrapper>
      {/* Title */}
      <motion.h2
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        style={{
          fontSize: "24px",
          color: "var(--accent-cyan)",
          textShadow: "0 0 12px rgba(0, 255, 224, 0.4)",
          marginBottom: "24px",
          textAlign: "center",
        }}
      >
        FIND YOUR PHOTOS
      </motion.h2>

      {/* Upload Zone */}
      <motion.div {...fadeUp} className="w-full mb-24">
        <DropZone
          label="Upload Your Selfie"
          sublabel="1–4 photos · drag & drop or click"
          maxFiles={4}
          onFiles={handleFiles}
          accept="image/*"
        />
      </motion.div>

      {/* Download All */}
      {hasResults && (
        <motion.div {...fadeUp} className="mb-24" style={{ textAlign: "center" }}>
          <RetroButton variant="secondary" onClick={downloadAll}>
            ↓ Download All Photos
          </RetroButton>
        </motion.div>
      )}

      {/* Loading Skeleton */}
      {loading && (
        <motion.div {...fadeUp} className="w-full mb-24">
          <SkeletonGrid count={8} />
        </motion.div>
      )}

      {/* Strong Matches */}
      {images.strong.length > 0 && (
        <motion.section {...fadeUp} className="w-full mb-32">
          <h3 className="section-title section-title--cyan">YOUR PHOTOS</h3>
          <div className="image-grid">
            {images.strong.map((img, idx) => {
              const flatIndex = idx;
              const isLast =
                idx === images.strong.length - 1 &&
                images.weak.length === 0;

              return (
                <div
                  key={`s-${idx}`}
                  ref={isLast ? lastImageRef : null}
                  className="image-grid__item image-grid__item--cyan"
                  onClick={() => setSelectedIndex(flatIndex)}
                >
                  <img
                    src={getImageUrl(eventId, img.imageId)}
                    alt={`Match ${idx + 1}`}
                    className="image-grid__img"
                    loading="lazy"
                  />
                </div>
              );
            })}
          </div>
        </motion.section>
      )}

      {/* Weak Matches */}
      {images.weak.length > 0 && (
        <motion.section {...fadeUp} className="w-full mb-32">
          <h3 className="section-title section-title--magenta">MAYBE YOU</h3>
          <div className="image-grid">
            {images.weak.map((img, idx) => {
              const flatIndex = images.strong.length + idx;
              const isLast = idx === images.weak.length - 1;

              return (
                <div
                  key={`w-${idx}`}
                  ref={isLast ? lastImageRef : null}
                  className="image-grid__item image-grid__item--magenta"
                  onClick={() => setSelectedIndex(flatIndex)}
                >
                  <img
                    src={getImageUrl(eventId, img.imageId)}
                    alt={`Maybe ${idx + 1}`}
                    className="image-grid__img"
                    loading="lazy"
                  />
                </div>
              );
            })}
          </div>
        </motion.section>
      )}

      {/* Image Modal */}
      <ImageModal
        images={allImagesFlat}
        selectedIndex={selectedIndex}
        onClose={() => setSelectedIndex(null)}
        onNavigate={setSelectedIndex}
        getImageSrc={(img) => getImageUrl(eventId, img.imageId)}
        getDownloadHref={(img) => getImageUrl(eventId, img.imageId)}
      />
    </PageWrapper>
  );
}
