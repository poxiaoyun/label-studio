/**
 * @deprecated It was used only without FF_3873 in old interface.
 */

import { inject, observer } from "mobx-react";
import { IconBan, IconInfoOutline } from "@humansignal/icons";
import { Button, Tooltip } from "@humansignal/ui";
import { cn } from "../../utils/bem";
import { isDefined } from "../../utils/utilities";

import "./Controls.scss";
import { useCallback, useMemo, useState } from "react";
import { t } from "@humansignal/i18n";

const TOOLTIP_DELAY = 0.8;

const ButtonTooltip = inject("store")(
  observer(({ store, title, children }) => {
    return (
      <Tooltip title={title} disabled={!store.settings.enableTooltips}>
        {children}
      </Tooltip>
    );
  }),
);

const controlsInjector = inject(({ store }) => {
  return {
    store,
    history: store?.annotationStore?.selected?.history,
  };
});

export const Controls = controlsInjector(
  observer(({ store, history, annotation }) => {
    const isReview = store.hasInterface("review");

    const historySelected = isDefined(store.annotationStore.selectedHistory);
    const { userGenerate, sentUserGenerate, versions, results, editable } = annotation;
    const buttons = [];

    const [isInProgress, setIsInProgress] = useState(false);

    // const isReady = store.annotationStore.selected.objects.every(object => object.isReady === undefined || object.isReady);
    const disabled = !editable || store.isSubmitting || historySelected || isInProgress; // || !isReady;
    const submitDisabled = store.hasInterface("annotations:deny-empty") && results.length === 0;

    const buttonHandler = useCallback(
      async (e, callback, tooltipMessage) => {
        const { addedCommentThisSession, currentComment, commentFormSubmit, inputRef } = store.commentStore;

        if (isInProgress) return;
        setIsInProgress(true);
        if (!inputRef.current || addedCommentThisSession) {
          callback();
        } else if ((currentComment ?? "").trim()) {
          e.preventDefault();
          await commentFormSubmit();
          callback();
        } else {
          const commentsInput = inputRef.current;

          store.commentStore.setTooltipMessage(tooltipMessage);
          commentsInput.scrollIntoView({
            behavior: "smooth",
          });
          commentsInput.focus({ preventScroll: true });
        }
        setIsInProgress(false);
      },
      [
        store.rejectAnnotation,
        store.skipTask,
        store.commentStore.currentComment,
        store.commentStore.inputRef,
        store.commentStore.commentFormSubmit,
        store.commentStore.addedCommentThisSession,
        isInProgress,
      ],
    );

    const RejectButton = useMemo(() => {
      return (
        <ButtonTooltip key="reject" title={t("lsf.components.top_bar.controls.reject_annotation_ctrl_space")}>
          <Button
            aria-label={t("lsf.components.top_bar.controls.reject_current_annotation")}
            disabled={disabled}
            look="danger"
            onClick={async (e) => {
              if (store.hasInterface("comments:reject") ?? true) {
                buttonHandler(e, () => store.rejectAnnotation({}), "Please enter a comment before rejecting");
              } else {
                console.log("rejecting");
                await store.commentStore.commentFormSubmit();
                store.rejectAnnotation({});
              }
            }}
          >
            {t("lsf.components.top_bar.controls.reject")}
          </Button>
        </ButtonTooltip>
      );
    }, [disabled, store]);

    if (isReview) {
      buttons.push(RejectButton);

      buttons.push(
        <ButtonTooltip key="accept" title={t("lsf.components.top_bar.controls.accept_annotation_ctrl_enter")}>
          <Button
            aria-label={t("lsf.components.top_bar.controls.accept_current_annotation")}
            disabled={disabled}
            look="primary"
            onClick={async () => {
              await store.commentStore.commentFormSubmit();
              store.acceptAnnotation();
            }}
          >
            {history.canUndo || annotation.versions.draft ? "Fix + Accept" : "Accept"}
          </Button>
        </ButtonTooltip>,
      );
    } else if (annotation.skipped) {
      buttons.push(
        <div className={cn("controls").elem("skipped-info").toClassName()} key="skipped">
          <IconBan color="#d00" /> {t("lsf.components.top_bar.controls.was_skipped")}
        </div>,
      );
      buttons.push(
        <ButtonTooltip key="cancel-skip" title={t("lsf.components.top_bar.controls.cancel_skip")}>
          <Button
            aria-label={t("lsf.components.top_bar.controls.cancel_skip_and_return_to")}
            disabled={disabled}
            look="outlined"
            onClick={async () => {
              await store.commentStore.commentFormSubmit();
              store.unskipTask();
            }}
          >
            {t("lsf.components.top_bar.controls.cancel_skip_2")}
          </Button>
        </ButtonTooltip>,
      );
    } else {
      // Manager roles that can force-skip unskippable tasks (OW=Owner, AD=Admin, MA=Manager)
      const MANAGER_ROLES = ["OW", "AD", "MA"];

      if (store.hasInterface("skip")) {
        const task = store.task;

        const isEnterprise = window.APP_SETTINGS?.billing?.enterprise;
        const skipDisabled = isEnterprise ? task?.allow_skip === false : false;
        const userRole = window.APP_SETTINGS?.user?.role;
        const hasForceSkipPermission = MANAGER_ROLES.includes(userRole);
        const canSkip = !skipDisabled || hasForceSkipPermission;
        const isDisabled = disabled || !canSkip;

        const tooltip = canSkip ? "Cancel (skip) task: [ Ctrl+Space ]" : "This task cannot be skipped";

        const showInfoIcon = skipDisabled && hasForceSkipPermission;

        if (showInfoIcon) {
          buttons.push(
            <Tooltip key="skip-info" title={t("lsf.components.top_bar.controls.annotators_and_reviewers_will_not")}>
              <IconInfoOutline width={20} height={20} className="text-neutral-content ml-auto cursor-pointer" />
            </Tooltip>,
          );
        }

        buttons.push(
          <ButtonTooltip key="skip" title={tooltip}>
            <Button
              aria-label={t("lsf.components.top_bar.controls.skip_current_task")}
              disabled={isDisabled}
              variant="negative"
              look="outlined"
              onClick={async (e) => {
                if (!canSkip) return;
                if (store.hasInterface("comments:skip") ?? true) {
                  buttonHandler(e, () => store.skipTask({}), "Please enter a comment before skipping");
                } else {
                  await store.commentStore.commentFormSubmit();
                  store.skipTask({});
                }
              }}
            >
              {t("lsf.components.top_bar.controls.skip")}
            </Button>
          </ButtonTooltip>,
        );
      }

      if ((userGenerate && !sentUserGenerate) || (store.explore && !userGenerate && store.hasInterface("submit"))) {
        const title = submitDisabled ? "Empty annotations denied in this project" : "Save results: [ Ctrl+Enter ]";
        // span is to display tooltip for disabled button

        buttons.push(
          <ButtonTooltip key="submit" title={title}>
            <div className={cn("controls").elem("tooltip-wrapper").toClassName()}>
              <Button
                aria-label={t("lsf.components.top_bar.controls.submit_current_annotation")}
                disabled={disabled || submitDisabled}
                look="primary"
                onClick={async () => {
                  await store.commentStore.commentFormSubmit();
                  store.submitAnnotation();
                }}
              >
                {t("lsf.components.top_bar.controls.submit")}
              </Button>
            </div>
          </ButtonTooltip>,
        );
      }

      if ((userGenerate && sentUserGenerate) || (!userGenerate && store.hasInterface("update"))) {
        const isUpdate = sentUserGenerate || versions.result;
        const button = (
          <ButtonTooltip key="update" title={t("lsf.components.top_bar.controls.update_this_task_alt_enter")}>
            <Button
              aria-label={t("lsf.components.top_bar.controls.update_current_annotation")}
              disabled={disabled || submitDisabled}
              look="primary"
              onClick={async () => {
                await store.commentStore.commentFormSubmit();
                store.updateAnnotation();
              }}
            >
              {isUpdate ? "Update" : "Submit"}
            </Button>
          </ButtonTooltip>
        );

        buttons.push(button);
      }
    }

    return (
      <div className={cn("controls").toClassName()}>
        <div className="grid grid-flow-col auto-cols-fr gap-tight items-center">{buttons}</div>
      </div>
    );
  }),
);
