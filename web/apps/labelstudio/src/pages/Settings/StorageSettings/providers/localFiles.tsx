import { z } from "zod";
import type { ProviderConfig } from "@humansignal/app-common/blocks/StorageProviderForm/types/provider";
import { IconFolderOpen } from "@humansignal/icons";
import { Alert, AlertDescription, AlertTitle } from "@humansignal/shad/components/ui/alert";
import { t } from "@humansignal/i18n";

const localFilesDocumentRoot =
  typeof window === "undefined" ? undefined : window.APP_SETTINGS?.local_files_document_root;
const localFilesServingEnabled =
  typeof window === "undefined" ? true : window.APP_SETTINGS?.local_files_serving_enabled !== false;
const isCommunityEdition =
  typeof window === "undefined" ? false : window.APP_SETTINGS?.version?.edition === "Community";
const trimTrailingSeparators = (value?: string) => value?.replace(/[/\\]+$/, "");
const defaultPathExample = localFilesDocumentRoot
  ? `${trimTrailingSeparators(localFilesDocumentRoot)}/your-subdirectory`
  : undefined;

const pathSchema = defaultPathExample
  ? z.string().min(1, "Path is required").default(defaultPathExample)
  : z.string().min(1, "Path is required");

const LocalFilesServingWarning = () => {
  if (localFilesServingEnabled) return null;
  return (
    <>
      <Alert variant="destructive">
        <AlertTitle>{t("pages.storage_settings.providers.local_files.local_file_serving_is_disabled")}</AlertTitle>
        <AlertDescription>
          {t("pages.storage_settings.providers.local_files.set_the_local_files_serving_enabled_environment_")}{" "}
          <a href="https://labelstud.io/guide/storage.html#Local-storage" target="_blank" rel="noreferrer">
            {t("pages.storage_settings.providers.local_files.local_storage_documentation")}
          </a>
          {isCommunityEdition && (
            <Alert variant="info">
              <AlertDescription>
                <p>
                  {t("pages.storage_settings.providers.local_files.tip_create_a_mydata_or")}
                </p>
                <p>
                  If you run the Docker image, the app starts in "/label-studio", so you can bind-mount your host folder
                  to "/label-studio/mydata" or "/label-studio/label-studio-data" inside the container to enable local
                  file serving without extra configuration.
                </p>
              </AlertDescription>
            </Alert>
          )}
        </AlertDescription>
      </Alert>
    </>
  );
};

export const localFilesProvider: ProviderConfig = {
  name: "localfiles",
  title: "Local Files",
  description: "Configure your local file storage connection with all required Label Studio settings",
  icon: () => (
    <IconFolderOpen
      width={40}
      height={40}
      style={{
        color: "var(--color-accent-canteloupe-base)",
        filter: "drop-shadow(0px 0px 12px var(--color-accent-canteloupe-base))",
      }}
    />
  ),
  fields: [
    {
      name: "serving_warning",
      type: "message",
      content: LocalFilesServingWarning,
    },
    {
      name: "path",
      type: "text",
      label: "Absolute local path",
      required: true,
      placeholder: defaultPathExample || "/data/my-folder/subdirectory",
      schema: pathSchema,
      defaultValue: defaultPathExample,
      description: `This path must be an absolute path on the host machine where Label Studio is running and start with \n"${localFilesDocumentRoot}" (LOCAL_FILES_DOCUMENT_ROOT).`,
    },
  ],
  layout: [{ fields: ["serving_warning"] }, { fields: ["path"] }],
};

export default localFilesProvider;
