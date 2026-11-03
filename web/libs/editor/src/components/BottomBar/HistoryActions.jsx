import { observer } from "mobx-react";
import { IconRedo, IconReset, IconUndo } from "@humansignal/icons";
import { Tooltip, Button } from "@humansignal/ui";
import { cn } from "../../utils/bem";
import "./HistoryActions.scss";
import { t } from "@humansignal/i18n";

export const EditingHistory = observer(({ entity }) => {
  const { history } = entity;

  return (
    <div className={cn("history-buttons").toClassName()}>
      <Tooltip title={t("lsf.components.bottom_bar.history_actions.undo")}>
        <Button
          variant="neutral"
          size="small"
          aria-label={t("lsf.components.bottom_bar.history_actions.undo")}
          look="string"
          disabled={!history?.canUndo}
          onClick={() => entity.undo()}
          className="aspect-square"
          leading={<IconUndo />}
          data-testid="bottombar-undo-button"
        />
      </Tooltip>
      <Tooltip title={t("lsf.components.bottom_bar.history_actions.redo")}>
        <Button
          variant="neutral"
          size="small"
          look="string"
          aria-label={t("lsf.components.bottom_bar.history_actions.redo")}
          disabled={!history?.canRedo}
          onClick={() => entity.redo()}
          className="aspect-square"
          leading={<IconRedo />}
          data-testid="bottombar-redo-button"
        />
      </Tooltip>
      <Tooltip title={t("lsf.components.bottom_bar.history_actions.reset")}>
        <Button
          variant="negative"
          look="string"
          size="small"
          aria-label={t("lsf.components.bottom_bar.history_actions.reset")}
          disabled={!history?.canUndo}
          onClick={() => history?.reset()}
          className="aspect-square"
          leading={<IconReset />}
          data-testid="bottombar-reset-button"
        />
      </Tooltip>
    </div>
  );
});
