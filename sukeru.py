import logging
from pathlib import Path
from PIL import Image, ImageDraw
from typing import Tuple, List

# ログの設定（実行状況を見やすく表示するなの）
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ImageMatteProcessor:
    """
    画像の背景をクロマキー技術を用いて透過処理するクラスです。
    特にAI生成画像によくある「市松模様の背景」を除去するのに適しています。
    """

    def __init__(self, input_dir: str, output_dir: str, threshold: int = 100):
        self.input_path = Path(input_dir)
        self.output_path = Path(output_dir)
        self.threshold = threshold
        # クロマキー用の一時的な色（鮮やかな緑）
        self.chroma_color = (0, 255, 0)
        
        # 出力ディレクトリがなければ作成
        self.output_path.mkdir(parents=True, exist_ok=True)

    def process_directory(self) -> None:
        """指定されたディレクトリ内の全画像を処理します。"""
        logger.info(f"処理開始: {self.input_path} -> {self.output_path}")
        
        # 画像ファイルを検索
        image_files = list(self.input_path.glob('*.[pP][nN][gG]')) + \
                      list(self.input_path.glob('*.[jJ][pP][gG]')) + \
                      list(self.input_path.glob('*.[jJ][pP][eE][gG]'))

        if not image_files:
            logger.warning("処理対象の画像が見つかりませんでした。")
            return

        for img_path in image_files:
            try:
                self._process_single_image(img_path)
            except Exception as e:
                logger.error(f"エラー発生 ({img_path.name}): {e}")

        logger.info("全画像の処理が完了しました。")

    def _process_single_image(self, img_path: Path) -> None:
        """単一の画像を読み込み、透過処理を行って保存します。"""
        with Image.open(img_path) as img:
            # RGBAモード（透明度あり）に変換
            img = img.convert("RGBA")
            width, height = img.size

            # 1. 四隅からFloodFillを行い、背景と推定される部分を緑色に塗りつぶす
            # AI画像特有の「背景の市松模様」を塗りつぶすための処理
            seed_points = [
                (0, 0), (width-1, 0), 
                (0, height-1), (width-1, height-1)
            ]
            
            # ImageDrawを使って塗りつぶし実行
            for pt in seed_points:
                ImageDraw.floodfill(img, pt, self.chroma_color + (255,), thresh=self.threshold)

            # 2. 緑色の部分を透明(Alpha=0)に置換する
            datas = img.getdata()
            new_data: List[Tuple[int, int, int, int]] = []

            for item in datas:
                # RGBがクロマキー色(0, 255, 0)と一致するか判定
                if item[0] == 0 and item[1] == 255 and item[2] == 0:
                    new_data.append((255, 255, 255, 0))  # 透明にする
                else:
                    new_data.append(item)

            img.putdata(new_data)

            # 保存（ファイル名の末尾に識別子をつける）
            output_file = self.output_path / f"{img_path.stem}_transparent.png"
            img.save(output_file, "PNG")
            logger.info(f"保存完了: {output_file.name}")

if __name__ == "__main__":
    # ここを変えるだけで別のフォルダも処理できるように設計
    BASE_PATH = Path(__file__).resolve().parent
    INPUT_DIR = BASE_PATH / "images"
    OUTPUT_DIR = BASE_PATH / "output"

    processor = ImageMatteProcessor(INPUT_DIR, OUTPUT_DIR)
    processor.process_directory()