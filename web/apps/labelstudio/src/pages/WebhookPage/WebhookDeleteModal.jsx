import { Button } from "@humansignal/ui";
import { modal } from "../../components/Modal/Modal";
import { useModalControls } from "../../components/Modal/ModalPopup";
import { Space } from "../../components/Space/Space";
import { cn } from "../../utils/bem";
import { t } from "@humansignal/i18n";

export const WebhookDeleteModal = ({ onDelete }) => {
  return modal({
    title: "Delete",
    body: () => {
      const ctrl = useModalControls();
      const rootClass = cn("webhook-delete-modal");
      return (
        <div className={rootClass}>
          <div className={rootClass.elem("modal-text").toClassName()}>
            {t("pages.pages.webhook_page.webhook_delete_modal.are_you_sure_you_want")}
          </div>
        </div>
      );
    },
    footer: () => {
      const ctrl = useModalControls();
      const rootClass = cn("webhook-delete-modal");
      return (
        <Space align="end">
          <Button
            look="outlined"
            onClick={() => {
              ctrl.hide();
            }}
            aria-label={t("pages.pages.webhook_page.webhook_delete_modal.cancel_webhook_deletion")}
          >
            {t("pages.pages.webhook_page.webhook_delete_modal.cancel")}
          </Button>
          <Button
            variant="negative"
            onClick={async () => {
              await onDelete();
              ctrl.hide();
            }}
            aria-label={t("pages.pages.webhook_page.webhook_delete_modal.confirm_webhook_deletion")}
          >
            {t("pages.pages.webhook_page.webhook_delete_modal.delete_webhook")}
          </Button>
        </Space>
      );
    },
    style: { width: 512 },
  });
};
