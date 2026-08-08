import AppKit

let root = URL(fileURLWithPath: FileManager.default.currentDirectoryPath)
let leftURL = root.appendingPathComponent("blog/images/the-odyssey-official-poster.jpg")
let rightURL = root.appendingPathComponent("blog/images/spider-man-brand-new-day-official-poster-hires.jpg")
let outputURL = root.appendingPathComponent("blog/images/odyssey-vs-spider-man-brand-new-day-on-x.jpg")

guard
    let leftImage = NSImage(contentsOf: leftURL),
    let rightImage = NSImage(contentsOf: rightURL)
else {
    fputs("Missing poster input.\n", stderr)
    exit(1)
}

let canvasSize = NSSize(width: 1600, height: 900)
let image = NSImage(size: canvasSize)
image.lockFocus()

let rect = NSRect(origin: .zero, size: canvasSize)

let gradient = NSGradient(colors: [
    NSColor(calibratedRed: 0.06, green: 0.08, blue: 0.14, alpha: 1),
    NSColor(calibratedRed: 0.16, green: 0.08, blue: 0.15, alpha: 1),
    NSColor(calibratedRed: 0.07, green: 0.15, blue: 0.29, alpha: 1)
])!
gradient.draw(in: rect, angle: 0)

NSColor(calibratedWhite: 1, alpha: 0.05).setFill()
NSBezierPath(roundedRect: NSRect(x: 70, y: 82, width: 1460, height: 736), xRadius: 42, yRadius: 42).fill()

let labelParagraph = NSMutableParagraphStyle()
labelParagraph.alignment = .left

let labelAttrs: [NSAttributedString.Key: Any] = [
    .font: NSFont.systemFont(ofSize: 20, weight: .bold),
    .foregroundColor: NSColor(calibratedRed: 0.51, green: 0.95, blue: 0.67, alpha: 1),
    .paragraphStyle: labelParagraph
]

let titleAttrs: [NSAttributedString.Key: Any] = [
    .font: NSFont.systemFont(ofSize: 56, weight: .heavy),
    .foregroundColor: NSColor.white,
    .paragraphStyle: labelParagraph
]

let subtitleAttrs: [NSAttributedString.Key: Any] = [
    .font: NSFont.systemFont(ofSize: 24, weight: .medium),
    .foregroundColor: NSColor(calibratedWhite: 1, alpha: 0.82),
    .paragraphStyle: labelParagraph
]

NSString(string: "MYMOVIEJAM AUDIENCE PULSE").draw(in: NSRect(x: 110, y: 785, width: 500, height: 28), withAttributes: labelAttrs)
NSString(string: "ODYSSEY vs SPIDER-MAN:\nBRAND NEW DAY").draw(in: NSRect(x: 110, y: 618, width: 1180, height: 138), withAttributes: titleAttrs)
NSString(string: "Independent X sentiment read • two event movies, two different highs").draw(in: NSRect(x: 110, y: 586, width: 900, height: 34), withAttributes: subtitleAttrs)

func drawPosterCard(image: NSImage, frame: NSRect, accent: NSColor, title: String, rating: String, note: String) {
    NSColor(calibratedWhite: 1, alpha: 0.92).setFill()
    NSBezierPath(roundedRect: frame, xRadius: 34, yRadius: 34).fill()

    let shadow = NSShadow()
    shadow.shadowBlurRadius = 18
    shadow.shadowOffset = NSSize(width: 0, height: -6)
    shadow.shadowColor = NSColor(calibratedWhite: 0, alpha: 0.18)
    shadow.set()

    let imageFrame = NSRect(x: frame.minX + 28, y: frame.minY + 106, width: frame.width - 56, height: frame.height - 162)
    NSColor(calibratedRed: 0.05, green: 0.06, blue: 0.09, alpha: 1).setFill()
    NSBezierPath(roundedRect: imageFrame, xRadius: 24, yRadius: 24).fill()

    let imageSize = image.size
    let aspect = min(imageFrame.width / imageSize.width, imageFrame.height / imageSize.height)
    let drawSize = NSSize(width: imageSize.width * aspect, height: imageSize.height * aspect)
    let drawRect = NSRect(
        x: imageFrame.midX - drawSize.width / 2,
        y: imageFrame.midY - drawSize.height / 2,
        width: drawSize.width,
        height: drawSize.height
    )
    image.draw(in: drawRect)

    let titleAttrs: [NSAttributedString.Key: Any] = [
        .font: NSFont.systemFont(ofSize: 25, weight: .bold),
        .foregroundColor: NSColor(calibratedRed: 0.08, green: 0.09, blue: 0.12, alpha: 1)
    ]
    NSString(string: title).draw(in: NSRect(x: frame.minX + 28, y: frame.minY + 58, width: frame.width - 56, height: 32), withAttributes: titleAttrs)

    let pillRect = NSRect(x: frame.minX + 28, y: frame.minY + 18, width: 230, height: 30)
    accent.setFill()
    NSBezierPath(roundedRect: pillRect, xRadius: 15, yRadius: 15).fill()
    let pillAttrs: [NSAttributedString.Key: Any] = [
        .font: NSFont.systemFont(ofSize: 15, weight: .bold),
        .foregroundColor: NSColor(calibratedRed: 0.05, green: 0.05, blue: 0.07, alpha: 1)
    ]
    NSString(string: rating).draw(in: NSRect(x: pillRect.minX + 16, y: pillRect.minY + 6, width: pillRect.width - 24, height: 18), withAttributes: pillAttrs)

    let noteAttrs: [NSAttributedString.Key: Any] = [
        .font: NSFont.systemFont(ofSize: 15, weight: .medium),
        .foregroundColor: NSColor(calibratedRed: 0.36, green: 0.39, blue: 0.45, alpha: 1)
    ]
    NSString(string: note).draw(in: NSRect(x: frame.minX + 276, y: frame.minY + 20, width: frame.width - 304, height: 24), withAttributes: noteAttrs)
}

drawPosterCard(
    image: leftImage,
    frame: NSRect(x: 110, y: 122, width: 590, height: 470),
    accent: NSColor(calibratedRed: 0.94, green: 0.82, blue: 0.47, alpha: 1),
    title: "The Odyssey",
    rating: "Audience pulse: 9.3/10",
    note: "Prestige awe • repeat IMAX energy"
)

drawPosterCard(
    image: rightImage,
    frame: NSRect(x: 780, y: 122, width: 590, height: 470),
    accent: NSColor(calibratedRed: 0.99, green: 0.56, blue: 0.41, alpha: 1),
    title: "Spider-Man: Brand New Day",
    rating: "Audience pulse: 9.0/10",
    note: "Emotional crowd-pleaser • rewatchable"
)

let footerAttrs: [NSAttributedString.Key: Any] = [
    .font: NSFont.systemFont(ofSize: 18, weight: .semibold),
    .foregroundColor: NSColor(calibratedWhite: 1, alpha: 0.76)
]
NSString(string: "Current MyMovieJam read: Odyssey wins the awe lane. Brand New Day wins the feel-good superhero lane.").draw(
    in: NSRect(x: 110, y: 74, width: 1280, height: 28),
    withAttributes: footerAttrs
)

image.unlockFocus()

guard
    let tiffData = image.tiffRepresentation,
    let rep = NSBitmapImageRep(data: tiffData),
    let jpegData = rep.representation(using: .jpeg, properties: [.compressionFactor: 0.9])
else {
    fputs("Failed to encode output image.\n", stderr)
    exit(1)
}

try jpegData.write(to: outputURL)
print("Wrote \(outputURL.path)")
