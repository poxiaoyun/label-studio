import { Badge } from "@humansignal/ui";
import { t } from "@humansignal/i18n";

const parseBoolean = (value) => {
  if ([true, 1, "true", "1", "yes"].includes(value) || !!value === true) {
    return true;
  }
  return false;
};

export const BooleanCell = (column) => {
  const boolValue = parseBoolean(column.value);

  if (boolValue === true) {
    return <Badge variant="positive">{t("dm.components.cell_views.boolean_cell.true")}</Badge>;
  }
  if (boolValue === false) {
    return <Badge variant="negative">{t("dm.components.cell_views.boolean_cell.false")}</Badge>;
  }

  return null;
};

BooleanCell.userSelectable = false;
