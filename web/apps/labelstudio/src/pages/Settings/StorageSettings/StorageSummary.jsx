import { format } from "date-fns/esm";
import { Button, CodeBlock, IconFileCopy, Space, Tooltip } from "@humansignal/ui";
import { DescriptionList } from "../../../components/DescriptionList/DescriptionList";
import { modal } from "../../../components/Modal/Modal";
import { Oneof } from "../../../components/Oneof/Oneof";
import { getLastTraceback } from "../../../utils/helpers";
import { useCopyText } from "@humansignal/core";
import { t, getLanguage } from "@humansignal/i18n";

// Component to handle copy functionality within the modal
const CopyButton = ({ msg }) => {
  const [copyText, copied] = useCopyText({ defaultText: msg });

  return (
    <Button variant="neutral" icon={<IconFileCopy />} onClick={() => copyText()} disabled={copied} className="w-[7rem]">
      {copied ? t("storage.summary.copied") : t("storage.summary.copy")}
    </Button>
  );
};

export const StorageSummary = ({ target, storage, className, storageTypes = [] }) => {
  const STATUS_KEYS = {
    initialized: "storage.status.initialized",
    queued: "storage.status.queued",
    in_progress: "storage.status.in_progress",
    failed: "storage.status.failed",
    completed_with_errors: "storage.status.completed_with_errors",
    completed: "storage.status.completed",
  };
  const storageStatus = STATUS_KEYS[storage.status] ? t(STATUS_KEYS[storage.status]) : storage.status;
  const last_sync_count = storage.last_sync_count ? storage.last_sync_count : 0;

  const tasks_existed =
    typeof storage.meta?.tasks_existed !== "undefined" && storage.meta?.tasks_existed !== null
      ? storage.meta.tasks_existed
      : 0;
  const total_annotations =
    typeof storage.meta?.total_annotations !== "undefined" && storage.meta?.total_annotations !== null
      ? storage.meta.total_annotations
      : 0;

  // help text for tasks and annotations
  const tasks_added_help = t("storage.summary.tasks_added_help", { count: last_sync_count });
  const tasks_total_help = [
    t("storage.summary.tasks_total_help", { count: tasks_existed }),
    t("storage.summary.tasks_added_total_help", { count: tasks_existed + last_sync_count }),
  ].join("\n");
  const annotations_help = t("storage.summary.annotations_help", { count: last_sync_count });
  const total_annotations_help =
    typeof storage.meta?.total_annotations !== "undefined"
      ? t("storage.summary.annotations_seen_help", { count: storage.meta.total_annotations })
      : "";

  const handleButtonClick = () => {
    const msg =
      `Error logs for ${target === "export" ? "export " : ""}${storage.type} ` +
      `storage ${storage.id} in project ${storage.project} and job ${storage.last_sync_job}:\n\n` +
      `${getLastTraceback(storage.traceback)}\n\n` +
      `meta = ${JSON.stringify(storage.meta)}\n`;

    const currentModal = modal({
      title: t("storage.summary.error_log_title"),
      body: <CodeBlock code={msg} variant="negative" className="max-h-[50vh] overflow-y-auto" />,
      footer: (
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
          {!window.APP_SETTINGS?.whitelabel_is_active && (
            <div>
              <>
                <a
                  href="https://labelstud.io/guide/storage.html#Troubleshooting"
                  target="_blank"
                  rel="noreferrer noopener"
                  aria-label={t("pages.settings.storage_settings.storage_summary.learn_more_about_cloud_storage")}
                >
                  {t("pages.settings.storage_settings.storage_summary.see_docs")}
                </a>{" "}
                {t("storage.summary.troubleshooting")}
              </>
            </div>
          )}
          <Space>
            <CopyButton msg={msg} />
            <Button variant="primary" className="w-[7rem]" onClick={() => currentModal.close()}>
              {t("pages.settings.storage_settings.storage_summary.close")}
            </Button>
          </Space>
        </div>
      ),
      style: { width: "700px" },
      optimize: false,
      allowClose: true,
    });
  };

  return (
    <div className={className}>
      <DescriptionList>
        <DescriptionList.Item term={t("storage.summary.term_type")}>
          {(storageTypes ?? []).find((s) => s.name === storage.type)?.title ?? storage.type}
        </DescriptionList.Item>

        <Oneof value={storage.type}>
          <SummaryS3 case={["s3", "s3s"]} storage={storage} />
          <GSCStorage case="gcs" storage={storage} />
          <AzureStorage case="azure" storage={storage} />
          <RedisStorage case="redis" storage={storage} />
          <LocalStorage case="localfiles" storage={storage} />
          <MohaStorage case="moha" storage={storage} />
        </Oneof>

        <DescriptionList.Item
          term={t("storage.summary.term_status")}
          help={[
            t("storage.status.help_initialized"),
            t("storage.status.help_queued"),
            t("storage.status.help_in_progress"),
            t("storage.status.help_failed"),
            t("storage.status.help_completed_with_errors"),
            t("storage.status.help_completed"),
          ].join("\n")}
        >
          {storage.status === "failed" || storage.status === "completed_with_errors" ? (
            <span
              className="cursor-pointer border-b border-dashed border-negative-border-subtle text-negative-content"
              onClick={handleButtonClick}
            >
              {storageStatus} {t("pages.settings.storage_settings.storage_summary.view_logs")}
            </span>
          ) : (
            storageStatus
          )}
        </DescriptionList.Item>

        {target === "export" ? (
          <DescriptionList.Item
            term={t("storage.summary.term_annotations")}
            help={`${annotations_help}\n${total_annotations_help}`}
          >
            <Tooltip title={annotations_help}>
              <span>{last_sync_count}</span>
            </Tooltip>
            <Tooltip title={total_annotations_help}>
              <span> {t("storage.summary.total_suffix", { count: total_annotations })}</span>
            </Tooltip>
          </DescriptionList.Item>
        ) : (
          <DescriptionList.Item
            term={t("storage.summary.term_tasks")}
            help={`${tasks_added_help}\n${tasks_total_help}`}
          >
            <Tooltip title={`${tasks_added_help}\n${tasks_total_help}`} style={{ whiteSpace: "pre-wrap" }}>
              <span>{last_sync_count + tasks_existed}</span>
            </Tooltip>
            <Tooltip title={tasks_added_help}>
              <span> {t("storage.summary.new_suffix", { count: last_sync_count })}</span>
            </Tooltip>
          </DescriptionList.Item>
        )}

        <DescriptionList.Item term={t("storage.summary.term_last_sync")}>
          {storage.last_sync
            ? format(
                new Date(storage.last_sync),
                getLanguage() === "zh-CN" ? "yyyy年M月d日 ∙ HH:mm:ss" : "MMMM dd, yyyy ∙ HH:mm:ss",
              )
            : t("storage.summary.not_synced")}
        </DescriptionList.Item>
      </DescriptionList>
    </div>
  );
};

const SummaryS3 = ({ storage }) => {
  return <DescriptionList.Item term={t("storage.summary.term_bucket")}>{storage.bucket}</DescriptionList.Item>;
};

const GSCStorage = ({ storage }) => {
  return <DescriptionList.Item term={t("storage.summary.term_bucket")}>{storage.bucket}</DescriptionList.Item>;
};

const AzureStorage = ({ storage }) => {
  return <DescriptionList.Item term={t("storage.summary.term_container")}>{storage.container}</DescriptionList.Item>;
};

const RedisStorage = ({ storage }) => {
  return (
    <>
      <DescriptionList.Item term={t("storage.summary.term_path")}>{storage.path}</DescriptionList.Item>
      <DescriptionList.Item term={t("storage.summary.term_host")}>
        {storage.host}
        {storage.port ? `:${storage.port}` : ""}
      </DescriptionList.Item>
    </>
  );
};

const LocalStorage = ({ storage }) => {
  return <DescriptionList.Item term={t("storage.summary.term_path")}>{storage.path}</DescriptionList.Item>;
};

// [moha] repository-based storage summary
const MohaStorage = ({ storage }) => (
  <>
    <DescriptionList.Item term={t("storage.summary.term_repository")}>
      {storage.organization}/{storage.repo_name}
    </DescriptionList.Item>
    <DescriptionList.Item term={t("storage.summary.term_revision")}>{storage.revision || t("storage.summary.default_branch")}</DescriptionList.Item>
    {storage.prefix ? <DescriptionList.Item term={t("storage.summary.term_prefix")}>{storage.prefix}</DescriptionList.Item> : null}
  </>
);
