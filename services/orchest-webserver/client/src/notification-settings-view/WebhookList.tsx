import { IconButton } from "@/components/common/IconButton";
import { DataTable, DataTableColumn } from "@/components/DataTable";
import { useAppContext } from "@/contexts/AppContext";
import AddOutlinedIcon from "@mui/icons-material/AddOutlined";
import DeleteOutlineIcon from "@mui/icons-material/DeleteOutline";
import OpenInNewIcon from "@mui/icons-material/OpenInNew";
import WebhookIcon from "@mui/icons-material/Webhook";
import Box from "@mui/material/Box";
import Button from "@mui/material/Button";
import Chip from "@mui/material/Chip";
import Link from "@mui/material/Link";
import Stack from "@mui/material/Stack";
import Typography from "@mui/material/Typography";
import React from "react";
import { CreateWebhookDialog } from "./create-webhook-dialog/CreateWebhookDialog";
import {
  deleteSuscriber,
  NotificationWebhookSubscriber,
} from "./notification-webhooks";
import { useNotificationSettingsContext } from "./NotificationSettingsContext";
import { WebhookVerifiedCheck } from "./WebhookVerifiedCheck";

type WebhookRow = Pick<
  NotificationWebhookSubscriber,
  "uuid" | "url" | "name" | "verify_ssl"
>;

type WebhookColumn = WebhookRow & {
  verified: React.ReactNode;
  delete: React.ReactNode;
};

export const WebhookList = () => {
  const { setConfirm } = useAppContext();
  const { webhooks } = useNotificationSettingsContext();

  const [isOpen, setIsOpen] = React.useState(false);
  const onClose = React.useCallback(() => setIsOpen(false), []);

  const columns: DataTableColumn<WebhookRow, WebhookColumn>[] = [
    { id: "name", label: "Name", render: (row) => row.name || "-" },
    {
      id: "url",
      label: "URL",
      align: "left",
      render: (row) => {
        return (
          <Stack direction="row" alignItems="center">
            {row.url}
            {row.verify_ssl && (
              <Chip
                label="SSL"
                size="small"
                sx={{ marginLeft: (theme) => theme.spacing(1) }}
              />
            )}
          </Stack>
        );
      },
    },
    {
      id: "verified",
      label: "Connection",
      align: "left",
      render: (row) => <WebhookVerifiedCheck subscriberUuid={row.uuid} />,
    },
    {
      id: "delete",
      label: " ",
      render: (row) => {
        return (
          <IconButton
            title="Delete"
            onClick={() => {
              setConfirm("Notice", "", async (resolve) => {
                deleteSuscriber(row.uuid).then(() => resolve(true));
                return true;
              });
            }}
          >
            <DeleteOutlineIcon />
          </IconButton>
        );
      },
    },
  ];

  const webhookRows = webhooks.map(({ uuid, name, url, verify_ssl }) => ({
    uuid,
    name,
    url,
    verify_ssl,
  }));

  return (
    <Stack
      direction="column"
      spacing={2}
      sx={{
        margin: (theme) => theme.spacing(2, 0),
        width: "100%",
      }}
    >
      <Stack direction="row" alignItems="center">
        <WebhookIcon
          fontSize="small"
          sx={{ margin: (theme) => theme.spacing(0, 2) }}
        />
        <Typography component="h6" variant="subtitle1">
          Webhooks
        </Typography>
      </Stack>

      <Stack
        direction="column"
        spacing={2}
        sx={{ paddingLeft: (theme) => theme.spacing(6.5) }}
      >
        <Stack direction="row" sx={{ margin: (theme) => theme.spacing(2, 0) }}>
          <Typography variant="body2">
            {`Webhooks let you receive HTTP push notifications to a URL.`}
          </Typography>
          <Link
            variant="body2"
            sx={{
              display: "flex",
              flexDirection: "row",
              alignItems: "center",
              margin: (theme) => theme.spacing(0, 1),
            }}
          >
            {`Webhook docs `}
            <OpenInNewIcon
              sx={{
                fontSize: (theme) => theme.spacing(2),
                marginLeft: (theme) => theme.spacing(1),
              }}
            />
          </Link>
        </Stack>
        <DataTable<WebhookRow, WebhookColumn>
          id="webhook-list"
          hideSearch
          disablePagination
          tableContainerElevation={0}
          columns={columns}
          rows={webhookRows}
        />
        <Box>
          <CreateWebhookDialog isOpen={isOpen} onClose={onClose}>
            <Button
              startIcon={<AddOutlinedIcon />}
              sx={{
                padding: (theme) => theme.spacing(1, 2),
                marginBottom: (theme) => theme.spacing(2),
              }}
              onClick={() => setIsOpen(true)}
            >
              New webhook
            </Button>
          </CreateWebhookDialog>
        </Box>
      </Stack>
    </Stack>
  );
};