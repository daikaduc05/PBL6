import { Bell } from "lucide-react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";

// Landing spot for the header bell. The real list (read/delete/settings,
// backed by the notification service) arrives with the notification-ui
// branch — shipping the route first lets the home shell link somewhere
// stable instead of a 404.
export default function NotificationsPage() {
  return (
    <div className="mx-auto max-w-2xl">
      <Card>
        <CardHeader>
          <Bell className="size-6 text-primary" aria-hidden />
          <CardTitle>Thông báo</CardTitle>
          <CardDescription>
            Trung tâm thông báo đang được hoàn thiện — nhắc học hằng ngày, xác nhận thanh toán và
            các thông báo tài khoản sẽ hiển thị ở đây.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <p className="text-body-sm text-text-muted">
            Trong lúc chờ, bạn vẫn nhận được email cho các thông báo quan trọng.
          </p>
        </CardContent>
      </Card>
    </div>
  );
}
