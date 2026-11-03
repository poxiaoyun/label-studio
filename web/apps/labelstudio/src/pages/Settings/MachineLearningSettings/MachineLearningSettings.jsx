import { useCallback, useContext, useEffect, useState } from "react";
import { NavLink } from "react-router-dom";
import { Button, Typography, Spinner, EmptyState, SimpleCard } from "@humansignal/ui";
import { useUpdatePageTitle, createTitleFromSegments } from "@humansignal/core";
import { Form, Label, Toggle } from "../../../components/Form";
import { modal } from "../../../components/Modal/Modal";
import { IconModels, IconExternal } from "@humansignal/icons";
import { useAPI } from "../../../providers/ApiProvider";
import { ProjectContext } from "../../../providers/ProjectProvider";
import { MachineLearningList } from "./MachineLearningList";
import { CustomBackendForm } from "./Forms";
import { TestRequest } from "./TestRequest";
import { StartModelTraining } from "./StartModelTraining";
import "./MachineLearningSettings.scss";
import { t } from "@humansignal/i18n";

export const MachineLearningSettings = () => {
  const api = useAPI();
  const { project, fetchProject } = useContext(ProjectContext);
  const [backends, setBackends] = useState([]);
  const [loading, setLoading] = useState(false);
  const [loaded, setLoaded] = useState(false);

  useUpdatePageTitle(createTitleFromSegments([project?.title, "Model Settings"]));

  const fetchBackends = useCallback(async () => {
    setLoading(true);
    const models = await api.callApi("mlBackends", {
      params: {
        project: project.id,
        include_static: true,
      },
    });

    if (models) setBackends(models);
    setLoading(false);
    setLoaded(true);
  }, [project, setBackends]);

  const startTrainingModal = useCallback(
    (backend) => {
      const modalProps = {
        title: t("settings.ml.start_training"),
        style: { width: 760 },
        closeOnClickOutside: true,
        body: <StartModelTraining backend={backend} />,
      };

      modal(modalProps);
    },
    [project],
  );

  const showRequestModal = useCallback(
    (backend) => {
      const modalProps = {
        title: t("settings.ml.test_request"),
        style: { width: 760 },
        closeOnClickOutside: true,
        body: <TestRequest backend={backend} />,
      };

      modal(modalProps);
    },
    [project],
  );

  const showMLFormModal = useCallback(
    (backend) => {
      const action = backend ? "updateMLBackend" : "addMLBackend";
      const modalProps = {
        title: backend ? t("settings.ml.edit_model") : t("settings.ml.connect_model"),
        style: { width: 760 },
        closeOnClickOutside: false,
        body: (
          <CustomBackendForm
            action={action}
            backend={backend}
            project={project}
            onSubmit={() => {
              fetchBackends();
              modalRef.close();
            }}
          />
        ),
      };

      const modalRef = modal(modalProps);
    },
    [project, fetchBackends],
  );

  useEffect(() => {
    if (project.id) {
      fetchBackends();
    }
  }, [project.id]);

  return (
    <section>
      <div className="w-[42rem]">
        <Typography variant="headline" size="medium" className="mb-base">
          {t("pages.settings.machine_learning_settings.machine_learning_settings.model")}
        </Typography>
        {loading && <Spinner size={32} />}
        {loaded && backends.length === 0 && (
          <SimpleCard title="" className="bg-primary-background border-primary-border-subtler p-base">
            <EmptyState
              size="medium"
              variant="primary"
              icon={<IconModels />}
              title={t("pages.settings.machine_learning_settings.machine_learning_settings.lets_connect_your_first_model")}
              description="Connect a machine learning model to generate live predictions for your project. Compare predictions, accelerate labeling with automatic prelabeling, and direct your team to the most impactful tasks through active learning."
              actions={
                <Button
                  variant="primary"
                  look="filled"
                  onClick={() => showMLFormModal()}
                  aria-label={t("pages.settings.machine_learning_settings.machine_learning_settings.add_machine_learning_model")}
                >
                  {t("pages.settings.machine_learning_settings.machine_learning_settings.connect_model")}
                </Button>
              }
              footer={
                !window.APP_SETTINGS?.whitelabel_is_active && (
                  <Typography variant="label" size="small" className="text-primary-link">
                    <a
                      href="https://labelstud.io/guide/ml"
                      target="_blank"
                      rel="noopener noreferrer"
                      data-testid="ml-help-link"
                      aria-label={t("pages.settings.machine_learning_settings.machine_learning_settings.learn_more_about_machine_learning")}
                      className="inline-flex items-center gap-1 hover:underline"
                    >
                      {t("pages.settings.machine_learning_settings.machine_learning_settings.learn_more")}
                      <IconExternal width={16} height={16} />
                    </a>
                  </Typography>
                )
              }
            />
          </SimpleCard>
        )}
        <MachineLearningList
          onEdit={(backend) => showMLFormModal(backend)}
          onTestRequest={(backend) => showRequestModal(backend)}
          onStartTraining={(backend) => startTrainingModal(backend)}
          fetchBackends={fetchBackends}
          backends={backends}
        />

        {backends.length > 0 && (
          <div className="my-wide">
            <Typography size="small" className="text-neutral-content-subtler">
              {t("pages.settings.machine_learning_settings.machine_learning_settings.a_connected_model_has_been")}
            </Typography>
            <Typography size="small" className="text-neutral-content-subtler mt-base">
              {t("pages.settings.machine_learning_settings.machine_learning_settings.1_navigate_to_the")} <i>{t("pages.settings.machine_learning_settings.machine_learning_settings.data_manager")}</i>.
            </Typography>
            <Typography size="small" className="text-neutral-content-subtler mt-tighter">
              {t("pages.settings.machine_learning_settings.machine_learning_settings.2_select_the_desired_tasks")}
            </Typography>
            <Typography size="small" className="text-neutral-content-subtler mt-tighter">
              {t("pages.settings.machine_learning_settings.machine_learning_settings.3_click_on")} <i>{t("pages.settings.machine_learning_settings.machine_learning_settings.batch_predictions")}</i>{t("settings.ml.from_the_menu_prefix")}<i>{t("pages.settings.machine_learning_settings.machine_learning_settings.actions")}</i>{t("settings.ml.from_the_menu_suffix")}
            </Typography>
            <Typography size="small" className="text-neutral-content-subtler mt-base">
              {t("pages.settings.machine_learning_settings.machine_learning_settings.if_you_want_to_use")}{" "}
              <NavLink to="annotation" className="hover:underline">
                {t("pages.settings.machine_learning_settings.machine_learning_settings.annotation_settings")}
              </NavLink>
              .
            </Typography>
          </div>
        )}

        <Form
          action="updateProject"
          formData={{ ...project }}
          params={{ pk: project.id }}
          onSubmit={() => fetchProject()}
        >
          {backends.length > 0 && (
            <div className="p-wide border border-neutral-border rounded-md">
              <Form.Row columnCount={1}>
                <Label text={t("pages.settings.machine_learning_settings.machine_learning_settings.configuration")} large />

                <div>
                  <Toggle
                    label={t("pages.settings.machine_learning_settings.machine_learning_settings.start_model_training_on_annotation")}
                    description={t("pages.settings.machine_learning_settings.machine_learning_settings.this_option_will_send_a")}
                    name="start_training_on_annotation_update"
                  />
                </div>
              </Form.Row>
            </div>
          )}

          {backends.length > 0 && (
            <Form.Actions>
              <Form.Indicator>
                <span case="success">{t("pages.settings.machine_learning_settings.machine_learning_settings.saved")}</span>
              </Form.Indicator>
              <Button type="submit" look="primary" className="w-[120px]" aria-label={t("pages.settings.machine_learning_settings.machine_learning_settings.save_machine_learning_settings")}>
                {t("pages.settings.machine_learning_settings.machine_learning_settings.save")}
              </Button>
            </Form.Actions>
          )}
        </Form>
      </div>
    </section>
  );
};

MachineLearningSettings.title = t("settings.nav.model");
MachineLearningSettings.path = "/ml";
