import { z } from "zod";
import type { ProviderConfig } from "@humansignal/app-common/blocks/StorageProviderForm/types/provider";
import { IconCloudProviderMoha } from "@humansignal/icons";

// [moha] Moha (https://github.com/poxiaoyun/moha) repo storage provider.
// Field names must match the Django model fields in io_storages/moha/models.py —
// the form posts them straight to /api/storages/{type}.
export const mohaProvider: ProviderConfig = {
  name: "moha",
  title: "Moha",
  description: "Import from, or export annotations to, a Moha dataset or model repository",
  icon: IconCloudProviderMoha,
  prefixLabel: "Repository prefix",
  fields: [
    {
      name: "moha_endpoint",
      type: "text",
      label: "Endpoint",
      required: true,
      placeholder: "https://rune.example.com",
      description: "Base URL of the Moha service (without the /moha path)",
      resetConnection: false,
      schema: z.string().url("Endpoint must be a valid URL"),
    },
    {
      name: "moha_token",
      type: "password",
      label: "Access Token",
      required: true,
      placeholder: "Paste a Moha access token",
      autoComplete: "new-password",
      accessKey: true,
      schema: z.string().min(1, "Access token is required"),
    },
    {
      name: "organization",
      type: "text",
      label: "Organization",
      required: true,
      placeholder: "demo",
      schema: z.string().min(1, "Organization is required"),
    },
    {
      name: "repo_type",
      type: "select",
      label: "Repository Type",
      required: true,
      options: [
        { value: "datasets", label: "Dataset" },
        { value: "models", label: "Model" },
      ],
      schema: z.enum(["datasets", "models"]).default("datasets"),
    },
    {
      name: "repo_name",
      type: "text",
      label: "Repository",
      required: true,
      placeholder: "street-view",
      schema: z.string().min(1, "Repository is required"),
    },
    {
      name: "revision",
      type: "text",
      label: "Revision",
      placeholder: "main (default branch)",
      description: "Branch, tag or commit. Leave empty to follow the default branch",
      schema: z.string().optional().default(""),
    },
    {
      name: "prefix",
      type: "text",
      label: "Repository Prefix",
      placeholder: "path/to/files",
      description: "Directory inside the repository where annotations are written",
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
