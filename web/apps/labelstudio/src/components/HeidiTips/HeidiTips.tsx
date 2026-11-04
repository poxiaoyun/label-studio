import { type FC, memo } from "react";
import type { HeidiTipsProps } from "./types";
import { HeidiTip } from "./HeidiTip";
import { useRandomTip } from "./hooks";

// [pxs] these cards are enterprise upsell copy (English, links to HumanSignal
// docs) and this deployment has no enterprise edition; hiding them removes the
// last English blocks from the product UI. Flip to true to bring them back.
const SHOW_ENTERPRISE_TIPS = false;

export const HeidiTips: FC<HeidiTipsProps> = memo(({ collection }) => {
  const [tip, dismiss, onLinkClick] = useRandomTip(collection);

  if (!SHOW_ENTERPRISE_TIPS) return null;

  return tip && <HeidiTip tip={tip} onDismiss={dismiss} onLinkClick={onLinkClick} />;
});
