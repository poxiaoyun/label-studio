import { useMemo, useState } from "react";
import { useHistory } from "react-router";
import { Button, Typography, useToast } from "@humansignal/ui";
import { useUpdatePageTitle, createTitleFromSegments } from "@humansignal/core";
import { Label } from "../../components/Form";
import { modal } from "../../components/Modal/Modal";
import { useModalControls } from "../../components/Modal/ModalPopup";
import Input from "../../components/Form/Elements/Input/Input";
import { Space } from "../../components/Space/Space";
import { Spinner } from "../../components/Spinner/Spinner";
import { useAPI } from "../../providers/ApiProvider";
import { useProject } from "../../providers/ProjectProvider";
import { cn } from "../../utils/bem";
import { t } from "@humansignal/i18n";

export const DangerZone = () => {
  const { project } = useProject();
  const api = useAPI();
  const history = useHistory();
  const toast = useToast();
  const [processing, setProcessing] = useState(null);

  useUpdatePageTitle(createTitleFromSegments([project?.title, t("settings.nav.danger_zone")]));

  const showDangerConfirmation = ({ title, message, requiredWord, buttonText, onConfirm }) => {
    const isDev = process.env.NODE_ENV === "development";

    return modal({
      title,
      width: 600,
      allowClose: false,
      body: () => {
        const ctrl = useModalControls();
        const inputValue = ctrl?.state?.inputValue || "";

        return (
          <div>
            <Typography variant="body" size="medium" className="mb-tight">
              {message}
            </Typography>
            <Input
              label={t("settings.danger_zone.type_to_proceed", { word: requiredWord })}
              value={inputValue}
              onChange={(e) => ctrl?.setState({ inputValue: e.target.value })}
              autoFocus
              data-testid="danger-zone-confirmation-input"
              autoComplete="off"
            />
          </div>
        );
      },
      footer: () => {
        const ctrl = useModalControls();
        const inputValue = (ctrl?.state?.inputValue || "").trim().toLowerCase();
        const isValid = isDev || inputValue === requiredWord.toLowerCase();

        return (
          <Space align="end">
            <Button
              variant="neutral"
              look="outline"
              onClick={() => ctrl?.hide()}
              data-testid="danger-zone-cancel-button"
            >
              {t("pages.pages.settings.danger_zone.cancel")}
            </Button>
            <Button
              variant="negative"
              disabled={!isValid}
              onClick={async () => {
                await onConfirm();
                ctrl?.hide();
              }}
              data-testid="danger-zone-confirm-button"
            >
              {buttonText}
            </Button>
          </Space>
        );
      },
    });
  };

  const handleOnClick = (type) => () => {
    const actionConfig = {
      reset_cache: {
        title: t("settings.danger_zone.reset_cache"),
        message: (
          <>
            {t("pages.pages.settings.danger_zone.you_are_about_to_reset")} <strong>{project.title}</strong>{t("pages.pages.settings.danger_zone.this_action_cannot_be")}
          </>
        ),
        requiredWord: "cache",
        buttonText: t("settings.danger_zone.reset_cache"),
      },
      tabs: {
        title: t("settings.danger_zone.drop_all_tabs"),
        message: (
          <>
            {t("pages.pages.settings.danger_zone.you_are_about_to_drop")} <strong>{project.title}</strong>{t("pages.pages.settings.danger_zone.this_action_cannot_be")}
          </>
        ),
        requiredWord: "tabs",
        buttonText: t("settings.danger_zone.drop_all_tabs"),
      },
      project: {
        title: t("settings.danger_zone.delete_project"),
        message: (
          <>
            {t("pages.pages.settings.danger_zone.you_are_about_to_delete")} <strong>{project.title}</strong>{t("pages.pages.settings.danger_zone.this_action_cannot_be")}
          </>
        ),
        requiredWord: "delete",
        buttonText: t("settings.danger_zone.delete_project"),
      },
    };

    const config = actionConfig[type];

    if (!config) {
      return;
    }

    showDangerConfirmation({
      ...config,
      onConfirm: async () => {
        setProcessing(type);
        try {
          if (type === "reset_cache") {
            await api.callApi("projectResetCache", {
              params: {
                pk: project.id,
              },
            });
            toast.show({ message: t("settings.danger_zone.cache_reset_ok") });
          } else if (type === "tabs") {
            await api.callApi("deleteTabs", {
              body: {
                project: project.id,
              },
            });
            toast.show({ message: t("settings.danger_zone.tabs_dropped_ok") });
          } else if (type === "project") {
            await api.callApi("deleteProject", {
              params: {
                pk: project.id,
              },
            });
            toast.show({ message: t("settings.danger_zone.project_deleted_ok") });
            history.replace("/projects");
          }
        } catch (error) {
          toast.show({ message: t("settings.danger_zone.error", { message: error.message }), type: "error" });
        } finally {
          setProcessing(null);
        }
      },
    });
  };

  const buttons = useMemo(
    () => [
      {
        type: "annotations",
        disabled: true, //&& !project.total_annotations_number,
        label: t("settings.danger_zone.delete_n_annotations", { count: project.total_annotations_number }),
      },
      {
        type: "tasks",
        disabled: true, //&& !project.task_number,
        label: t("settings.danger_zone.delete_n_tasks", { count: project.task_number }),
      },
      {
        type: "predictions",
        disabled: true, //&& !project.total_predictions_number,
        label: t("settings.danger_zone.delete_n_predictions", { count: project.total_predictions_number }),
      },
      {
        type: "reset_cache",
        help: t("settings.danger_zone.reset_cache_help"),
        label: t("settings.danger_zone.reset_cache"),
      },
      {
        type: "tabs",
        help: t("settings.danger_zone.drop_all_tabs_help"),
        label: t("settings.danger_zone.drop_all_tabs"),
      },
      {
        type: "project",
        help: t("settings.danger_zone.delete_project_help"),
        label: t("settings.danger_zone.delete_project"),
      },
    ],
    [project],
  );

  return (
    <div className={cn("simple-settings").toClassName()}>
      <Typography variant="headline" size="medium" className="mb-tighter">
        {t("pages.pages.settings.danger_zone.danger_zone")}
      </Typography>
      <Typography variant="body" size="medium" className="text-neutral-content-subtler !mb-base">
        {t("pages.pages.settings.danger_zone.perform_these_actions_at_your")}
      </Typography>

      {project.id ? (
        <div style={{ marginTop: 16 }}>
          {buttons.map((btn) => {
            const waiting = processing === btn.type;
            const disabled = btn.disabled || (processing && !waiting);

            return (
              btn.disabled !== true && (
                <div className={cn("settings-wrapper").toClassName()} key={btn.type}>
                  <Typography variant="title" size="large">
                    {btn.label}
                  </Typography>
                  {btn.help && <Label description={btn.help} style={{ width: 600, display: "block" }} />}
                  <Button
                    key={btn.type}
                    variant="negative"
                    look="outlined"
                    disabled={disabled}
                    waiting={waiting}
                    onClick={handleOnClick(btn.type)}
                    style={{ marginTop: 16 }}
                  >
                    {btn.label}
                  </Button>
                </div>
              )
            );
          })}
        </div>
      ) : (
        <div style={{ display: "flex", justifyContent: "center", marginTop: 32 }}>
          <Spinner size={32} />
        </div>
      )}
    </div>
  );
};

DangerZone.title = t("settings.nav.danger_zone");
DangerZone.path = "/danger-zone";
