import { Badge, Button, Select, Typography, Tooltip, EnterpriseBadge } from "@humansignal/ui";
import { useCallback, useContext } from "react";
import { IconSpark } from "@humansignal/icons";
import { Form, Input, TextArea } from "../../components/Form";
import { RadioGroup } from "../../components/Form/Elements/RadioGroup/RadioGroup";
import { ProjectContext } from "../../providers/ProjectProvider";
import { cn } from "../../utils/bem";
import { HeidiTips } from "../../components/HeidiTips/HeidiTips";
import { FF_LSDV_E_297, isFF } from "../../utils/feature-flags";
import { createURL } from "../../components/HeidiTips/utils";
import { t } from "@humansignal/i18n";

export const GeneralSettings = () => {
  const { project, fetchProject } = useContext(ProjectContext);

  const updateProject = useCallback(() => {
    if (project.id) fetchProject(project.id, true);
  }, [project]);

  const colors = ["#FDFDFC", "#FF4C25", "#FF750F", "#ECB800", "#9AC422", "#34988D", "#617ADA", "#CC6FBE"];

  const samplings = [
    { value: "Sequential", label: "Sequential", description: "Tasks are ordered by Task ID" },
    { value: "Uniform", label: "Random", description: "Tasks are chosen with uniform random" },
  ];

  return (
    <div className={cn("general-settings").toClassName()}>
      <div className={cn("general-settings").elem("wrapper").toClassName()}>
        <h1>{t("pages.pages.settings.general_settings.general_settings")}</h1>
        <div className={cn("settings-wrapper").toClassName()}>
          <Form action="updateProject" formData={{ ...project }} params={{ pk: project.id }} onSubmit={updateProject}>
            <Form.Row columnCount={1} rowGap="16px">
              <Input name="title" label={t("pages.pages.settings.general_settings.project_name")} />

              <TextArea name="description" label={t("pages.pages.settings.general_settings.description")} style={{ minHeight: 128 }} />
              {isFF(FF_LSDV_E_297) && (
                <div className={cn("workspace-placeholder").toClassName()}>
                  <div className={cn("workspace-placeholder").elem("badge-wrapper").toClassName()}>
                    <div className={cn("workspace-placeholder").elem("title").toClassName()}>{t("pages.pages.settings.general_settings.workspace")}</div>
                    <EnterpriseBadge size="small" className="ml-2" />
                  </div>
                  <Select placeholder={t("pages.pages.settings.general_settings.select_an_option")} disabled options={[]} />
                  <Typography size="small" className="my-tight">
                    {t("pages.pages.settings.general_settings.simplify_project_management_by_organizing")}{" "}
                    <a
                      target="_blank"
                      href={createURL(
                        "https://docs.humansignal.com/guide/manage_projects#Create-workspaces-to-organize-projects",
                        {
                          experiment: "project_settings_tip",
                          treatment: "simplify_project_management",
                        },
                      )}
                      rel="noreferrer"
                      className="underline hover:no-underline"
                    >
                      {t("pages.pages.settings.general_settings.learn_more")}
                    </a>
                  </Typography>
                </div>
              )}
              <RadioGroup name="color" label={t("pages.pages.settings.general_settings.color")} size="large" labelProps={{ size: "large" }}>
                {colors.map((color) => (
                  <RadioGroup.Button key={color} value={color}>
                    <div className={cn("color").toClassName()} style={{ "--background": color }} />
                  </RadioGroup.Button>
                ))}
              </RadioGroup>

              <RadioGroup label={t("pages.pages.settings.general_settings.task_sampling")} labelProps={{ size: "large" }} name="sampling" simple>
                {samplings.map(({ value, label, description }) => (
                  <RadioGroup.Button
                    key={value}
                    value={`${value} sampling`}
                    label={`${label} sampling`}
                    description={description}
                  />
                ))}
                {isFF(FF_LSDV_E_297) && (
                  <RadioGroup.Button
                    key="uncertainty-sampling"
                    value=""
                    label={
                      <>
                        {t("pages.pages.settings.general_settings.uncertainty_sampling")}{" "}
                        <Tooltip title={t("pages.pages.settings.general_settings.available_on_label_studio_enterprise")}>
                          <Badge
                            variant="enterprise"
                            icon={<IconSpark />}
                            size="small"
                            style="ghost"
                            className="ml-tightest"
                          />
                        </Tooltip>
                      </>
                    }
                    disabled
                    description={
                      <>
                        {t("pages.pages.settings.general_settings.tasks_are_chosen_according_to")}{" "}
                        <a
                          target="_blank"
                          href={createURL("https://docs.humansignal.com/guide/active_learning", {
                            experiment: "project_settings_workspace",
                            treatment: "workspaces",
                          })}
                          rel="noreferrer"
                        >
                          {t("pages.pages.settings.general_settings.learn_more")}
                        </a>
                      </>
                    }
                  />
                )}
              </RadioGroup>
            </Form.Row>

            <Form.Actions>
              <Form.Indicator>
                <span case="success">{t("pages.pages.settings.general_settings.saved")}</span>
              </Form.Indicator>
              <Button type="submit" className="w-[150px]" aria-label={t("pages.pages.settings.general_settings.save_general_settings")}>
                {t("pages.pages.settings.general_settings.save")}
              </Button>
            </Form.Actions>
          </Form>
        </div>
      </div>
      {isFF(FF_LSDV_E_297) && <HeidiTips collection="projectSettings" />}
    </div>
  );
};

GeneralSettings.menuItem = "General";
GeneralSettings.path = "/";
GeneralSettings.exact = true;
