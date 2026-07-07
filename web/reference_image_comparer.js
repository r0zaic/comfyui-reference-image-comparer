import { app } from "../../scripts/app.js";
import { api } from "../../scripts/api.js";

const CLASS_NAME = "ReferenceImageComparer";

function viewUrl(data) {
  const params = new URLSearchParams({
    filename: data.filename,
    subfolder: data.subfolder ?? "",
    type: data.type ?? "temp",
  });
  return api.apiURL(`/view?${params.toString()}`);
}

// The reference_image combo value can be "sub/dir/name.png" or "name.png [input]".
function parseInputValue(value) {
  let type = "input";
  let filename = String(value);
  const annotated = filename.match(/^(.*) \[(input|output|temp)\]$/);
  if (annotated) {
    filename = annotated[1];
    type = annotated[2];
  }
  let subfolder = "";
  const idx = filename.lastIndexOf("/");
  if (idx >= 0) {
    subfolder = filename.slice(0, idx);
    filename = filename.slice(idx + 1);
  }
  return { filename, subfolder, type };
}

function loadImg(src, node) {
  const img = new Image();
  img.onload = () => node.setDirtyCanvas(true, false);
  img.src = src;
  return img;
}

const ready = (img) => img && img.complete && img.naturalWidth > 0;

app.registerExtension({
  name: "ReferenceImageComparer.ui",
  async beforeRegisterNodeDef(nodeType, nodeData) {
    if (nodeData.name !== CLASS_NAME) return;

    const onNodeCreated = nodeType.prototype.onNodeCreated;
    nodeType.prototype.onNodeCreated = function () {
      onNodeCreated?.apply(this, arguments);
      const node = this;
      const referenceWidget = node.widgets?.find((w) => w.name === "reference_image");

      const widget = {
        type: "refcompare",
        name: "comparer",
        value: "",
        serialize: false,
        options: { serialize: false },
        split: 0.5,
        imgA: null,
        imgB: null,
        rect: null, // last drawn image rect, node-local coords
        _loadedFor: null,

        setImages(aList, bList) {
          if (aList?.[0]) this.imgA = loadImg(viewUrl(aList[0]), node);
          if (bList?.[0]) this.imgB = loadImg(viewUrl(bList[0]), node);
          else this.imgB = null;
        },

        computeSize(width) {
          return [width ?? 240, 300];
        },

        draw(ctx, node, width, y) {
          // Suppress the default upload-preview so it doesn't draw under us.
          if (node.imgs?.length) node.imgs = null;

          // Preview the picked reference image even before the first run.
          const picked = referenceWidget?.value;
          if (picked && picked !== this._loadedFor) {
            this._loadedFor = picked;
            this.imgA = loadImg(viewUrl(parseInputValue(picked)), node);
          }

          const margin = 8;
          const availW = width - margin * 2;
          const availH = node.size[1] - y - margin;
          this.rect = null;

          const base = ready(this.imgB) ? this.imgB : ready(this.imgA) ? this.imgA : null;
          if (!base || availW < 16 || availH < 16) {
            ctx.save();
            ctx.fillStyle = "#888";
            ctx.font = "12px Arial";
            ctx.textAlign = "center";
            ctx.fillText("run the workflow to compare", width / 2, y + Math.max(availH, 24) / 2);
            ctx.restore();
            return;
          }

          const scale = Math.min(availW / base.naturalWidth, availH / base.naturalHeight);
          const dw = base.naturalWidth * scale;
          const dh = base.naturalHeight * scale;
          const dx = margin + (availW - dw) / 2;
          const dy = y + (availH - dh) / 2;
          this.rect = { x: dx, y: dy, w: dw, h: dh };

          ctx.save();
          const both = ready(this.imgA) && ready(this.imgB);
          if (ready(this.imgB)) ctx.drawImage(this.imgB, dx, dy, dw, dh);
          if (ready(this.imgA)) {
            if (both) {
              const splitX = dx + dw * this.split;
              ctx.save();
              ctx.beginPath();
              ctx.rect(dx, dy, splitX - dx, dh);
              ctx.clip();
              ctx.drawImage(this.imgA, dx, dy, dw, dh);
              ctx.restore();
              ctx.strokeStyle = "rgba(255,255,255,0.9)";
              ctx.lineWidth = 2;
              ctx.beginPath();
              ctx.moveTo(splitX, dy);
              ctx.lineTo(splitX, dy + dh);
              ctx.stroke();
            } else {
              ctx.drawImage(this.imgA, dx, dy, dw, dh);
            }
          }

          ctx.font = "11px Arial";
          ctx.textBaseline = "top";
          const label = (text, x, align) => {
            ctx.textAlign = align;
            const w = ctx.measureText(text).width;
            const bx = align === "left" ? x : x - w;
            ctx.fillStyle = "rgba(0,0,0,0.55)";
            ctx.fillRect(bx - 3, dy + 3, w + 6, 16);
            ctx.fillStyle = "#fff";
            ctx.fillText(text, x, dy + 6);
          };
          if (ready(this.imgA)) label("reference", dx + 6, "left");
          if (ready(this.imgB)) label("result", dx + dw - 6, "right");
          ctx.restore();
        },

        mouse(event, pos) {
          if (!this.rect) return false;
          if (event.type === "pointerdown" || event.type === "pointermove") {
            this.split = Math.min(1, Math.max(0, (pos[0] - this.rect.x) / this.rect.w));
            node.setDirtyCanvas(true, false);
            return true;
          }
          return false;
        },
      };

      node.__comparerWidget = widget;
      node.addCustomWidget(widget);

      // Swipe on hover (no click needed), like rgthree's comparer.
      const onMouseMove = node.onMouseMove;
      node.onMouseMove = function (e, pos) {
        onMouseMove?.apply(this, arguments);
        const r = widget.rect;
        if (r && pos && pos[1] >= r.y && pos[1] <= r.y + r.h) {
          widget.split = Math.min(1, Math.max(0, (pos[0] - r.x) / r.w));
          this.setDirtyCanvas(true, false);
        }
      };

      node.setSize([Math.max(node.size[0], 280), Math.max(node.size[1], 400)]);
    };

    const onExecuted = nodeType.prototype.onExecuted;
    nodeType.prototype.onExecuted = function (message) {
      onExecuted?.apply(this, arguments);
      this.__comparerWidget?.setImages(message?.a_images, message?.b_images);
      this.setDirtyCanvas(true, false);
    };
  },
});
