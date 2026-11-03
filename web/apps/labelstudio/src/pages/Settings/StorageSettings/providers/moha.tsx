import { z } from "zod";
import type { ProviderConfig } from "@humansignal/app-common/blocks/StorageProviderForm/types/provider";
import { IconCloudProviderMoha } from "@humansignal/icons";
import { t } from "@humansignal/i18n";

// [moha] Moha (https://github.com/poxiaoyun/moha) repo storage provider.
// Field names must match the Django model fields in io_storages/moha/models.py —
// the form posts them straight to /api/storages/{type}.
export const mohaProvider: ProviderConfig = {
  name: "moha",
  title: "Moha",
  description: t("providers.moha.description"),
  icon: IconCloudProviderMoha,
  prefixLabel: t("providers.moha.prefix_label"),
  fields: [
    {
      name: "moha_endpoint",
      type: "text",
      label: t("providers.moha.endpoint"),
      required: true,
      placeholder: "https://rune.example.com",
      description: t("providers.moha.endpoint_help"),
      resetConnection: false,
      schema: z.string().url(t("providers.moha.endpoint_error")),
    },
    {
      name: "moha_token",
      type: "password",
      label: t("providers.moha.token"),
      required: true,
      placeholder: t("providers.moha.token_placeholder"),
      autoComplete: "new-password",
      accessKey: true,
      schema: z.string().min(1, t("providers.moha.token_error")),
    },
    {
      name: "organization",
      type: "text",
      label: t("providers.moha.organization"),
      required: true,
      placeholder: "demo",
      schema: z.string().min(1, t("providers.moha.organization_error")),
    },
    {
      name: "repo_type",
      type: "select",
      label: t("providers.moha.repo_type"),
      required: true,
      options: [
        { value: "datasets", label: t("providers.moha.repo_type_dataset") },
        { value: "models", label: t("providers.moha.repo_type_model") },
      ],
      schema: z.enum(["datasets", "models"]).default("datasets"),
    },
    {
      name: "repo_name",
      type: "text",
      label: t("providers.moha.repository"),
      required: true,
      placeholder: "street-view",
      schema: z.string().min(1, t("providers.moha.repository_error")),
    },
    {
      name: "revision",
      type: "text",
      label: t("providers.moha.revision"),
      placeholder: t("providers.moha.revision_placeholder"),
      description: t("providers.moha.revision_help"),
      schema: z.string().optional().default(""),
    },
    {
      name: "prefix",
      type: "text",
      label: t("providers.moha.prefix"),
      placeholder: "path/to/files",
      description: t("providers.moha.prefix_help"),
      target: "export",
      schema: z.string().optional().default(""),
    },
  ],
  layout: [
    { fields: ["moha_endpoint"] },
    { fields: ["moha_token"] },
    { fields: ["organization", "repo_type"] },
    { fields: ["repo_name", "revision"] },
    { fields: ["prefix"] },
  ],
};
