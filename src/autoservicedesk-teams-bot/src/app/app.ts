import { App } from "@microsoft/teams.apps";
import { ChatPrompt } from "@microsoft/teams.ai";
import { LocalStorage } from "@microsoft/teams.common";
import { OpenAIChatModel } from "@microsoft/teams.openai";
import { MessageActivity, TokenCredentials } from "@microsoft/teams.api";
import { ManagedIdentityCredential } from "@azure/identity";
import * as fs from "fs";
import * as path from "path";
import config from "../config";
import axios from "axios"; // Importar axios para realizar la petición HTTP

// Create storage for conversation history
const storage = new LocalStorage();

// Load instructions from file on initialization
function loadInstructions(): string {
  const instructionsFilePath = path.join(__dirname, "instructions.txt");
  return fs.readFileSync(instructionsFilePath, "utf-8").trim();
}

// Load instructions once at startup
const instructions = loadInstructions();

const createTokenFactory = () => {
  return async (
    scope: string | string[],
    tenantId?: string
  ): Promise<string> => {
    const managedIdentityCredential = new ManagedIdentityCredential({
      clientId: process.env.CLIENT_ID,
    });
    const scopes = Array.isArray(scope) ? scope : [scope];
    const tokenResponse = await managedIdentityCredential.getToken(scopes, {
      tenantId: tenantId,
    });

    return tokenResponse.token;
  };
};

// Configure authentication using TokenCredentials
const tokenCredentials: TokenCredentials = {
  clientId: process.env.CLIENT_ID || "",
  token: createTokenFactory(),
};

const credentialOptions =
  config.MicrosoftAppType === "UserAssignedMsi"
    ? { ...tokenCredentials }
    : undefined;

// Create the app with storage
const app = new App({
  ...credentialOptions,
  storage,
});

// Handle incoming messages
app.on("message", async ({ send, stream, activity }) => {
  const conversationKey = `${activity.conversation.id}/${activity.from.id}`;
  const messages = storage.get(conversationKey) || [];

  try {
    const userRequest = activity.text; // Obtener el mensaje del usuario
    // Obtener el correo del usuario de una propiedad válida o usar un valor predeterminado
    const userEmail = activity.from?.id || "unknown@example.com";

    // Preparar los datos para la petición POST con un thread_id fijo
    const postData = {
      user_request: userRequest,
      user_email: "",
      thread_id: "",
    };

    // Realizar la petición POST a la API externa
    const apiResponse = await axios.post(
      "/support",
      postData
    );

    // Procesar la respuesta de la API
    const { thread_id, response } = apiResponse.data;

    // Enviar la respuesta al usuario en Teams
    const responseActivity = new MessageActivity(response)
      .addAiGenerated()
      .addFeedback();
    await send(responseActivity);

    // Guardar el historial de la conversación
    messages.push({ role: "user", content: userRequest });
    messages.push({ role: "assistant", content: response });
    storage.set(conversationKey, messages);
  } catch (error) {
    console.error(error);
    await send("The agent encountered an error or bug.");
    await send(
      "To continue to run this agent, please fix the agent source code."
    );
  }
});

app.on("message.submit.feedback", async ({ activity }) => {
  //add custom feedback process logic here
  console.log("Your feedback is " + JSON.stringify(activity.value));
});

export default app;
