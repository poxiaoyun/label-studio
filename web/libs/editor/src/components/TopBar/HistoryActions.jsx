import { observer } from "mobx-react";
import { IconRedo, IconRemove, IconUndo } from "@humansignal/icons";
import { Button } from "@humansignal/ui";
import { cn } from "../../utils/bem";
import "./HistoryActions.scss";
import { t } from "@humansignal/i18n";

export const EditingHistory = observer(({ entity }) => {
  const { history } = entity;

  return (
    <div className={cn("history-buttons").toClassName()}>
      <Button
        variant="neutral"
        look="string"
        aria-label={t("lsf.components.top_bar.history_actions.undo")}
        className="!p-0"
        tooltip={t("lsf.components.top_bar.history_actions.undo")}
        disabled={!history?.canUndo}
        onClick={() => entity.undo()}
      >
        <IconUndo />
      </Button>
      <Button
        variant="neutral"
        look="string"
        aria-label={t("lsf.components.top_bar.history_actions.redo")}
        className="!p-0"
        tooltip={t("lsf.components.top_bar.history_actions.redo")}
        disabled={!history?.canRedo}
        onClick={() => entity.redo()}
        leading={<IconRedo />}
      />
      <Button
        look="string"
        variant="negative"
        aria-label={t("lsf.components.top_bar.history_actions.reset")}
        tooltip={t("lsf.components.top_bar.history_actions.reset")}
        className="!p-0"
        disabled={!history?.canUndo}
        onClick={() => history?.reset()}
        leading={<IconRemove />}
      />
    </div>
  );
});
