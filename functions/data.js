let dataStore = [];

exports.handler = async (event) => {
  if (event.httpMethod === "GET") {
    return {
      statusCode: 200,
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ data: dataStore }),
    };
  }

  if (event.httpMethod === "POST") {
    try {
      const body = JSON.parse(event.body);
      dataStore.push(body);
      return {
        statusCode: 201,
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ status: "success", received: body }),
      };
    } catch (e) {
      return {
        statusCode: 400,
        body: JSON.stringify({ status: "error", detail: e.message }),
      };
    }
  }

  return { statusCode: 405, body: "Method Not Allowed" };
};
