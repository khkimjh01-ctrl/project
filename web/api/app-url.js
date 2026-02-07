// Vercel Serverless: 환경 변수 STREAMLIT_APP_URL 반환
module.exports = (req, res) => {
  res.setHeader('Access-Control-Allow-Origin', '*');
  const url = process.env.STREAMLIT_APP_URL || '';
  res.status(200).json({ url });
};
