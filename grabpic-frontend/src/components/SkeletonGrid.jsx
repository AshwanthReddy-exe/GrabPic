/**
 * SkeletonGrid — Shimmer loading grid with "Scanning film..." label.
 */
export default function SkeletonGrid({ count = 8 }) {
  return (
    <div className="w-full">
      <div className="skeleton-grid">
        {Array.from({ length: count }).map((_, i) => (
          <div key={i} className="skeleton-grid__item" />
        ))}
      </div>
      <div className="skeleton-grid__label">Scanning film...</div>
    </div>
  );
}
