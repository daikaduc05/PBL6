import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";
import { VipGate } from "@/components/feature/vip-gate";

describe("VipGate", () => {
  it("renders children when user is VIP", () => {
    render(
      <VipGate isVip={true}>
        <div data-testid="secret-content">Secret VIP Content</div>
      </VipGate>,
    );
    expect(screen.getByTestId("secret-content")).toBeInTheDocument();
    expect(screen.queryByText(/Nội dung dành riêng cho thành viên VIP/i)).not.toBeInTheDocument();
  });

  it("renders paywall when user is not VIP", () => {
    render(
      <VipGate isVip={false}>
        <div data-testid="secret-content">Secret VIP Content</div>
      </VipGate>,
    );
    expect(screen.queryByTestId("secret-content")).not.toBeInTheDocument();
    expect(screen.getByText(/Nội dung dành riêng cho thành viên VIP/i)).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /Nâng cấp VIP ngay/i })).toHaveAttribute(
      "href",
      "/checkout",
    );
  });
});
